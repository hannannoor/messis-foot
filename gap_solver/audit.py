"""Controlled behavior comparisons, without reading or scoring ground truth."""
from collections import Counter

from .core import Config, _blocks, infer, summary


def scorer_expanded_labels(frames, decisions):
    """Mirror official X filling inside grading blocks; this is not an accuracy score."""
    if len(frames) != len(decisions) or any(d.label not in ('H', 'A', 'D', 'X') for d in decisions):
        raise ValueError('audit requires one valid decision per original frame')
    labels = [d.label for d in decisions]
    for low, high in _blocks(frames):
        first = next((i for i in range(low, high) if labels[i] != 'X'), None)
        if first is None:
            continue
        previous = labels[first]
        for i in range(low, high):
            if labels[i] == 'X':
                labels[i] = previous
            else:
                previous = labels[i]
    return labels


def _spell_count(frames, labels):
    count = 0
    for low, high in _blocks(frames):
        previous = None
        for label in labels[low:high]:
            count += label in ('H', 'A') and label != previous
            previous = label
    return count


def compare_decisions(frames, before, after):
    old = scorer_expanded_labels(frames, before)
    new = scorer_expanded_labels(frames, after)
    active = [i for i, f in enumerate(frames) if f.period]
    changed = [i for i in active if before[i].label != after[i].label]
    return {
        'raw_label_changes': len(changed),
        'newly_assigned_frames': sum(before[i].label == 'X' and after[i].label != 'X' for i in changed),
        'newly_assigned_missing_ball_team_frames': sum(
            before[i].label == 'X' and after[i].label in ('H', 'A') and not frames[i].ball_observed
            for i in changed),
        'scorer_expanded_label_changes': sum(old[i] != new[i] for i in active),
        'propagated_changes_on_raw_unchanged_frames': sum(
            old[i] != new[i] and before[i].label == after[i].label for i in active),
        'raw_changes_without_scorer_effect': sum(old[i] == new[i] for i in changed),
        'label_transition_counts': dict(Counter(before[i].label+'->'+after[i].label for i in changed)),
        'changed_from_reason_counts': dict(Counter(before[i].reason for i in changed)),
        'changed_to_reason_counts': dict(Counter(after[i].reason for i in changed)),
        'possession_spells_before': _spell_count(frames, old),
        'possession_spells_after': _spell_count(frames, new),
        'accuracy_measured': False,
    }


def bridge_diagnostics(frames, decisions, cfg=Config()):
    """Explain remaining X runs after the existing bridge rules, without filling them."""
    if len(frames) != len(decisions):
        raise ValueError('bridge audit dimensions differ')
    intervals, counts, missing = Counter(), Counter(), 0
    for low, high in _blocks(frames):
        i = low
        while i < high:
            if decisions[i].label != 'X':
                i += 1
                continue
            start = i
            while i < high and decisions[i].label == 'X':
                missing += not frames[i].ball_observed
                i += 1
            segment = frames[start:i]
            left = decisions[start-1] if start > low else None
            right = decisions[i] if i < high else None
            if left is None or right is None:
                cause = 'unbounded_gap'
            elif any(f.restart_hint or f.dead_evidence for f in segment):
                cause = 'restart_or_dead_context'
            elif left.label not in ('H', 'A') or right.label not in ('H', 'A'):
                cause = 'non_team_anchor'
            elif left.label != right.label:
                cause = 'opposing_anchors'
            elif any(f.tag_team in ('H', 'A', 'CONFLICT') and f.tag_team != left.label for f in segment):
                cause = 'conflicting_tags'
            elif ((i-start)/cfg.fps > cfg.short_bridge_s and
                  ((i-start)/cfg.fps > cfg.tagged_bridge_s or
                   not all(f.tag_team == left.label for f in segment))):
                cause = 'duration_or_tag_support'
            else:
                cause = 'unsupported_or_unconfirmed_anchor'
            intervals[cause] += 1
            counts[cause] += i-start
    return {'intervals_by_cause': dict(intervals), 'frames_by_cause': dict(counts),
            'unresolved_missing_ball_frames': missing,
            'note': 'Diagnostic categories after existing rules; not new possession evidence.'}


def build_baseline_audit(raw_frames, corrected_frames, fused_decisions, cfg=Config()):
    if (len(raw_frames) != len(corrected_frames) or len(raw_frames) != len(fused_decisions)
            or any(a.period != b.period for a, b in zip(raw_frames, corrected_frames))):
        raise ValueError('controlled comparisons require identical frame and half indices')
    stages = {'legacy_tactical': infer(raw_frames, cfg, legacy_restart_veto=True),
              'restart_repaired': infer(raw_frames, cfg),
              'published_context': infer(corrected_frames, cfg)}
    report = {
        'accuracy_measured': False,
        'stages': {name: summary(raw_frames if name != 'published_context' else corrected_frames, decisions)
                   for name, decisions in stages.items()},
        'comparisons': {
            'restart_repair': compare_decisions(raw_frames, stages['legacy_tactical'], stages['restart_repaired']),
            'published_context': compare_decisions(corrected_frames, stages['restart_repaired'], stages['published_context']),
            'broadcast_fusion': compare_decisions(corrected_frames, stages['published_context'], fused_decisions),
            'total': compare_decisions(corrected_frames, stages['legacy_tactical'], fused_decisions),
        },
        'remaining_gap_diagnostics': bridge_diagnostics(corrected_frames, stages['published_context'], cfg),
        'note': 'Fixed-input behavior ablation. Scorer-expanded changes are not spellF1 or accuracy.',
    }
    return report, stages
