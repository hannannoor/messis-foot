"""Local clock-box selection; choosing a crop does not annotate possession."""
import json
import tempfile
from math import ceil, isfinite
from pathlib import Path

from .clock_ocr import _run, crop_filter, probe_video


def normalise_box(box, width, height, display_scale=1):
    if width <= 0 or height <= 0 or display_scale <= 0 or any(not isfinite(v) for v in box):
        raise ValueError('invalid selection dimensions')
    x0,x1 = sorted((box[0]*display_scale, box[2]*display_scale))
    y0,y1 = sorted((box[1]*display_scale, box[3]*display_scale))
    x0,x1 = max(0,min(width,x0)), max(0,min(width,x1))
    y0,y1 = max(0,min(height,y0)), max(0,min(height,y1))
    if x1-x0 < 8 or y1-y0 < 8:
        raise ValueError('Draw a larger box around the COMPLETE clock digits.')
    return x0/width, y0/height, (x1-x0)/width, (y1-y0)/height


def load_roi(path, source):
    config=json.loads(Path(path).read_text(encoding='utf-8'))
    if config.get('source') != source:
        raise ValueError('Saved clock box belongs to a different camera source')
    roi=tuple(float(v) for v in config['roi'])
    if len(roi) != 4:
        raise ValueError('Saved clock ROI needs four values')
    crop_filter(roi,0,1,1)
    return roi


def extract_reference_frame(video, frame, output, ffmpeg='ffmpeg', ffprobe='ffprobe'):
    count,_=probe_video(video,ffprobe)
    if not 0 <= frame < count:
        raise ValueError('Clock selection frame is outside video')
    _run([ffmpeg,'-hide_banner','-loglevel','error','-i',str(video),'-an',
          '-vf','select=eq(n\\,{})'.format(frame),'-frames:v','1','-update','1','-y',str(output)],3600)
    if not Path(output).is_file():
        raise ValueError('No reference frame was decoded')


def choose_roi(video, frame, source, save_path, ffmpeg='ffmpeg', ffprobe='ffprobe'):
    try:
        import tkinter as tk
    except ImportError as exc:
        raise ValueError('Clock selector needs tkinter. In this conda environment install: conda install tk') from exc
    print('Preparing one local reference frame for clock selection...',flush=True)
    with tempfile.TemporaryDirectory(prefix='local-clock-box-') as d:
        image_path=Path(d)/'reference.png'
        extract_reference_frame(video,frame,image_path,ffmpeg,ffprobe)
        try:
            window=tk.Tk()
        except tk.TclError as exc:
            raise ValueError('A local desktop display is needed for --select-roi') from exc
        window.title('Select clock digits - football pipeline')
        try:
            original=tk.PhotoImage(file=str(image_path))
            width,height=original.width(),original.height()
            max_width=max(320,min(1440,window.winfo_screenwidth()-100))
            max_height=max(180,min(700,window.winfo_screenheight()-330))
            factor=max(1,ceil(max(width/max_width,height/max_height)))
            shown=original.subsample(factor,factor)
            tk.Label(window,text='Drag around ALL the clock digits, with a small margin. Exclude the score.').pack(padx=10,pady=5)
            canvas=tk.Canvas(window,width=shown.width(),height=shown.height(),highlightthickness=0)
            canvas.pack()
            canvas.create_image(0,0,anchor='nw',image=shown)
            message=tk.StringVar(value='Drag a box. Inspect the enlarged preview below, then click Use clock box.')
            tk.Label(window,textvariable=message).pack(pady=3)
            preview=tk.Label(window)
            preview.pack(pady=3)
            selection=[None]
            accepted=[False]
            start=[0,0]
            rectangle=[None]
            preview_image=[None]
            buttons=tk.Frame(window)
            buttons.pack(pady=5)

            def accept():
                if selection[0] is not None:
                    accepted[0]=True
                    window.destroy()

            use_button=tk.Button(buttons,text='Use clock box',state='disabled',command=accept)
            use_button.pack(side='left',padx=5)
            tk.Button(buttons,text='Cancel',command=window.destroy).pack(side='left',padx=5)

            def press(event):
                start[:]=[event.x,event.y]
                selection[0]=None
                use_button.configure(state='disabled')
                if rectangle[0] is not None:
                    canvas.delete(rectangle[0])
                rectangle[0]=canvas.create_rectangle(event.x,event.y,event.x,event.y,outline='#ff3030',width=2)

            def drag(event):
                if rectangle[0] is not None:
                    canvas.coords(rectangle[0],start[0],start[1],event.x,event.y)

            def release(event):
                drag(event)
                try:
                    roi=normalise_box((start[0],start[1],event.x,event.y),width,height,factor)
                except ValueError as exc:
                    message.set(str(exc))
                    return
                x,y,w,h=roi
                left,top,right,bottom=round(x*width),round(y*height),round((x+w)*width),round((y+h)*height)
                zoom=max(1,min(4,600//max(1,right-left),100//max(1,bottom-top)))
                enlarged=tk.PhotoImage()
                enlarged.tk.call(str(enlarged),'copy',str(original),'-from',left,top,right,bottom,'-zoom',zoom,zoom)
                preview_image[0]=enlarged
                preview.configure(image=enlarged)
                selection[0]=roi
                message.set('Does the preview show the complete clock and exclude the score? Redraw if needed.')
                use_button.configure(state='normal')

            canvas.bind('<ButtonPress-1>',press)
            canvas.bind('<B1-Motion>',drag)
            canvas.bind('<ButtonRelease-1>',release)
            window.mainloop()
        finally:
            try:
                window.destroy()
            except tk.TclError:
                pass
        if not accepted[0] or selection[0] is None:
            raise ValueError('Clock-box selection cancelled. OCR was not run.')
        result={'source':source,'roi':list(selection[0]),'video_width':width,
                'video_height':height,'selection_frame':frame}
        path=Path(save_path)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print('Saved clock box: '+str(path),flush=True)
        return selection[0]
