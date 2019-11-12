import tkinter
from easydict import EasyDict as edict
from tkinter.filedialog import askdirectory,askopenfilename,asksaveasfilename
import os
from PIL import Image,ImageTk
import numpy as np
from concurrent.futures import ThreadPoolExecutor as tpe
from functools import lru_cache

pool=tpe(4)
tk=tkinter
shape=(1024,768)
args=edict({
    'input' : None,
    'output' : '',
    'cls_list':['0','1','2','3','4'],
    'filelist':[],
    'filelabel':{},
    'curlabel':-1,
    'curselect':0,
    'im':None,
    'imname':None,
    'imidx':-1,
    'clsidx':-1
})

class labeled(object):
    num=0

def clsbarGen():
    clsLB.delete(0,tk.END)
    for name in args.cls_list:
        clsLB.insert(tk.END,name)

def clsSelect(path=''):
    if len(path)==0:
        path=askopenfilename()
    if path is None or len(path)==0:
        return
    with open(path,encoding='utf-8') as f:
        args.cls_list=[i.strip() for i in f.readlines() if len(i.strip())>0]
    clsbarGen()
    initlistbox()

def readLabel(path=''):
    if len(path)==0:
        path=askopenfilename()
    if not os.path.exists(path):
        return
    with open(path,encoding='utf-8') as f:
        for r in f.readlines():
            if len(r)>1:
                k,v=r.strip().split(',')
                args.filelabel[k]=v

def saveLabel(path=''):
    labeled.num=0
    if len(path)==0:
        path=asksaveasfilename()
    if path is None or len(path)==0:
        return
    with open(path,'w',encoding='utf-8') as f:
        f.write('\n'.join(('{},{}'.format(k,v) for k,v in args.filelabel.items())))
    args.output=path

def getfilelist(path):
    args.filelist=[]
    for name in sorted(os.listdir(path)):
        _,ext=os.path.splitext(name)
        if ext.lower() in {'.jpg','.jpeg','.bmp','.png','.tif','.tiff'}:
            args.filelist.append(name)
    labeled.num = 0

def initlistbox():
    theLB.delete(0,tk.END)
    for idx,name in enumerate(args.filelist):
        if name in args.filelabel and args.filelabel[name] in args.cls_list:
            #theLB.insert(tk.END,'*_'+name)
            theLB.insert(tk.END, name)
            theLB.itemconfigure(idx,bg='#FFFFFF')
        else:
            #theLB.insert(tk.END,'__'+name)
            theLB.insert(tk.END,  name)
            theLB.itemconfigure(idx, bg='#FFBBBB')
    theLB.selection_set(0)
    drawImage()

def inputSelect():
    input=askdirectory()
    if len(input)==0:
        return
    args.input=input
    getfilelist(args.input)
    initlistbox()
    if os.path.exists(os.path.join(args.input,'classes.txt')):
        clsSelect(os.path.join(args.input,'classes.txt'))

def outputSelect():
    readLabel()
    initlistbox()

def saveSelect():
    saveLabel()

def resetCls(event=None):
    idx=args.imidx
    if idx >= 0:
        filename=args.filelist[idx]
        clsLB.selection_clear(0,tk.END)

        if filename in args.filelabel and args.filelabel[filename] in args.cls_list:
            clsLB.selection_set(args.cls_list.index(args.filelabel[filename]))
        clslabel.config(text=args.filelabel.get(filename,''))

def onClsChange(event=None):
    seidxs=clsLB.curselection()
    if args.imidx >= 0 and len(seidxs)>0:
        cls=args.cls_list[seidxs[0]]
        filename=args.filelist[args.imidx]
        #theLB.delete(args.imidx)
        #theLB.insert(args.imidx,'*_'+filename)
        theLB.itemconfigure(args.imidx, bg='#FFFFFF')
        theLB.selection_set(args.imidx)
        args.filelabel[filename]=cls
        clslabel.config(text=cls)
    labeled.num += 1
    if labeled.num > 100 and len(args.output) > 0:
        try:
            saveLabel(args.output)
        except Exception:
            pass

def loadImage(filepath):
    im = Image.open(filepath)
    ratio = max(float(im.width) / shape[0], float(im.height) / shape[1])
    im = im.resize((int(im.width / ratio), int(im.height / ratio)), resample=Image.BILINEAR)
    return im

@lru_cache(maxsize=64)
def loadImageBg(filepath):
    return pool.submit(loadImage,filepath)

def drawImage(event=None):
    idxs=theLB.curselection()
    if len(idxs)>0:
        idx=idxs[0]
        args.imidx=idx
        filename=args.filelist[idx]
        filepath=os.path.join(args.input,filename)
        if filepath != args.imname:
            fut=loadImageBg(filepath)
            if fut.done():
                im=fut.result()
            else:
                im=loadImage(filepath)
            args.im=ImageTk.PhotoImage(im)
            Label.config(image=args.im)
            args.imname=filepath
        for i in range(idx-4,idx+6):
            filename = args.filelist[i % len(args.filelist)]
            filepath = os.path.join(args.input, filename)
            loadImageBg(filepath)
    resetCls()

def changeFocus(event=None):
    binput.focus_set()

def onKeyDown(event=None):
    if event.keysym == 'Left' or event.keysym == 'Right':
        idx=args.imidx
        if idx>=0:
            if event.keysym == 'Left':
                new_idx=idx-1
            elif event.keysym == 'Right':
                new_idx=idx+1
            else:
                raise NotImplementedError
            new_idx=new_idx % len(args.filelist)
            theLB.selection_clear(0,tk.END)
            theLB.selection_set(new_idx)
            theLB.yview_scroll(new_idx-idx,'unit')
            drawImage()
    elif event.keysym == 'Up' or event.keysym == 'Down' or 96 <= event.keycode < 96 + len(args.cls_list):
        if 96 <= event.keycode < 96 + len(args.cls_list):
            new_idx=event.keycode-96
        else:
            seidxs = clsLB.curselection()
            if len(seidxs) == 0:
                new_idx=0 if event.keysym=='Down' else -1
            else:
                new_idx= seidxs[0] +1 if event.keysym=='Down' else seidxs[0]-1
            new_idx = new_idx % len(args.cls_list)
        clsLB.selection_clear(0,tk.END)
        clsLB.selection_set(new_idx)
        onClsChange()

root=tkinter.Tk()
root.title('图片类别标注工具，快捷键为方向键上下左右和小键盘数字键0-9')

# left: listbox
fm1 = tkinter.Frame(root)
scrolly=tkinter.Scrollbar(fm1)
theLB = tkinter.Listbox(fm1,width=18,height=15,yscrollcommand=scrolly.set,exportselection=False)
scrolly.config(command=theLB.yview)



# canvas
fmc = tkinter.Frame(root)
args.im= ImageTk.PhotoImage(Image.fromarray(np.zeros((shape[1],shape[0],3),dtype='uint8')+200))
Label = tk.Label(fmc,image=args.im, width=shape[0],height=shape[1],font=('System', 32))
clslabel = tk.Label(fmc,text='',font=(None,32),width=8,bg='#FFFFEE')

clsLB=tkinter.Listbox(root,width=10,height=12,exportselection=False,font=(None, 16))

#right:
fm2 = tkinter.Frame(root)
binput=tk.Button(fm2, text='选择图片路径',command=inputSelect)
bcls=tk.Button(fm2, text='载入类别信息',command=clsSelect)
boutput=tk.Button(fm2, text='载入标注文件',command=outputSelect)
bsave=tk.Button(fm2, text='保存当前标注',command=saveSelect)


# fm1

fm1.pack(side=tkinter.LEFT,fill=tkinter.BOTH,expand=tkinter.YES)
theLB.pack(side=tkinter.LEFT,fill=tkinter.BOTH,expand=tkinter.YES)
scrolly.pack(side=tkinter.LEFT,fill=tkinter.Y)

fmc.pack(side=tkinter.LEFT,fill=tkinter.NONE,expand=tkinter.NO)
clslabel.pack(side=tk.TOP,fill=tkinter.X,ipadx=5,ipady=5,padx=5,pady=5)
Label.pack(side=tk.TOP,fill=tk.NONE)

clsLB.pack(side=tk.TOP,fill=tkinter.NONE)



# fm2
fm2.pack(side=tkinter.TOP,fill=tkinter.Y,expand=tkinter.YES,ipadx=5,ipady=5,padx=5,pady=5)
binput.pack(side=tk.TOP, fill=tk.BOTH,ipadx=3,ipady=3,padx=3,pady=3,expand=tk.YES)
bcls.pack(side=tk.TOP, fill=tk.BOTH,ipadx=3,ipady=3,padx=3,pady=3,expand=tk.YES)
boutput.pack(side=tk.TOP, fill=tk.BOTH,ipadx=3,ipady=3,padx=3,pady=3,expand=tk.YES)
bsave.pack(side=tk.TOP, fill=tk.BOTH,ipadx=3,ipady=3,padx=3,pady=3,expand=tk.YES)


theLB.bind('<<ListboxSelect>>',drawImage)
clsLB.bind('<<ListboxSelect>>',onClsChange)
root.bind('<Key>',onKeyDown)
theLB.bind('<FocusIn>',changeFocus)
clsLB.bind('<FocusIn>',changeFocus)

clsbarGen()

root.mainloop()
