import tkinter
from voronoi import VoronoiDiagram

root = tkinter.Tk()
root.state('zoomed')
w, h = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry("%dx%d+0+0" % (w, h))
voronoi_diagram = VoronoiDiagram(root, width=w, height=h, borderwidth=0, highlightthickness=0, bg="black")
voronoi_diagram.pack()
root.update()
voronoi_diagram.init_diagram()

def task():
    voronoi_diagram.delete("all")
    voronoi_diagram.render()
    root.after(10, task)  # reschedule event in 2 seconds

root.after(10, task)
root.mainloop()