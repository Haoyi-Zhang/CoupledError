"""Draw the four finite-contract schematics as embedded-font vector PDFs."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

plt.rcParams.update({"font.family":"STIXGeneral", "mathtext.fontset":"stix",
                     "font.size":11, "pdf.fonttype":42, "ps.fonttype":42})


def canvas(size, limits):
    fig=plt.figure(figsize=size)
    ax=fig.add_axes((.02,.02,.96,.96))
    ax.set(xlim=limits[:2],ylim=limits[2:]);ax.axis("off")
    return fig,ax


def box(ax,x,y,label,w=2.7,h=.7,size=11,dashed=False):
    ax.add_patch(Rectangle((x-w/2,y-h/2),w,h,facecolor="white",edgecolor="black",
                           lw=.85,linestyle="--" if dashed else "-"))
    ax.text(x,y,label,ha="center",va="center",fontsize=size,linespacing=1.2)


def arrow(ax,a,b,dashed=False):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle="-|>",mutation_scale=10,
                                lw=.9,color="black",linestyle="--" if dashed else "-"))


def save(fig,path):
    fig.canvas.draw();renderer=fig.canvas.get_renderer();canvas_bounds=fig.bbox
    for ax in fig.axes:
        for t in ax.texts:
            b=t.get_window_extent(renderer)
            if b.x0<canvas_bounds.x0 or b.y0<canvas_bounds.y0 or b.x1>canvas_bounds.x1 or b.y1>canvas_bounds.y1:
                raise ValueError("Label outside canvas: "+t.get_text())
    path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path,metadata={"Creator":"Matplotlib","CreationDate":None,"ModDate":None},facecolor="white")
    plt.close(fig)


def order_context(path):
    fig,ax=canvas((6.4,3.5),(0,10,0,6.3))
    box(ax,2,5.6,"old contract $C$\nlaw $m(S,X)$")
    box(ax,8,5.6,"replacement $D$\nlaw $n(S,Y)$")
    box(ax,5,3.45,"frame law\n$q(S,R)$",w=2.1)
    box(ax,5,1.95,"monotone monitor\n$h(S,\\cdot,R)$",w=2.9)
    box(ax,2,1.95,r"$\mathcal{R}_C(q,h)$",w=1.9,h=.6)
    box(ax,8,1.95,r"$\mathcal{R}_D(q,h)$",w=1.9,h=.6)
    box(ax,5,.55,r"$\Delta(C,D)$",w=1.9,h=.6)
    arrow(ax,(2,5.25),(3.95,3.45));arrow(ax,(8,5.25),(6.05,3.45))
    ax.text(2.55,3.95,"$X$",ha="center",va="center")
    ax.text(7.45,3.95,"$Y$",ha="center",va="center")
    ax.plot([2,8],[4.95,4.95],ls="--",lw=.85,color="black")
    ax.text(5,4.55,"boundary-preserving order coupling",ha="center",va="center",fontsize=10.5)
    arrow(ax,(5,3.10),(5,2.30));ax.text(5.5,2.72,"$S,R$",ha="center",va="center")
    for x in (2,8):
        outer=1 if x==2 else 9
        ax.plot([outer,outer,x],[5.25,2.5,2.5],lw=.85,color="black")
        arrow(ax,(x,2.5),(x,2.25))
    arrow(ax,(3.55,1.95),(2.95,1.95));arrow(ax,(6.45,1.95),(7.05,1.95))
    arrow(ax,(2,1.65),(4.05,.55));arrow(ax,(8,1.65),(5.95,.55))
    save(fig,path)


def boolean_correlation(path):
    fig,ax=canvas((6.4,2.7),(-.3,10,-.35,3.7))
    pos={"00":(1.6,.2),"01":(.45,1.6),"10":(2.75,1.6),"11":(1.6,3.)}
    for u,v in (("00","01"),("00","10"),("01","11"),("10","11")):
        ax.plot([pos[u][0],pos[v][0]],[pos[u][1],pos[v][1]],lw=.9,color="black")
    for name,(x,y) in pos.items():
        ax.add_patch(Circle((x,y),.25,facecolor="white",edgecolor="black",lw=.9,zorder=2))
        ax.text(x,y,"$"+name+"$",ha="center",va="center",fontsize=11)
    box(ax,6.65,3.,r"$c_1=\frac{1}{2}\delta_{10}+\frac{1}{2}\delta_{11}$",w=4.5,h=.65)
    box(ax,6.65,2.1,r"$c_2=\delta_{01}$",w=4.5,h=.65)
    box(ax,6.65,1.2,r"$n=\frac{1}{2}\delta_{01}+\frac{1}{2}\delta_{10}$",w=4.5,h=.65)
    ax.text(6.65,.45,r"Fixed-upset gap $=0$; contextual loss $=\frac{1}{4}$",ha="center",va="center",fontsize=10.5)
    ax.text(6.65,-.06,r"$C=\mathrm{conv}\{c_1,c_2\}$",ha="center",va="center",fontsize=10.5)
    # Dashed links identify support membership, not transport mass.
    arrow(ax,(.45,1.85),(4.4,2.1),True)
    arrow(ax,(3.0,1.6),(4.4,1.2),True)
    save(fig,path)


def dependency_scopes(path):
    fig,ax=canvas((6.4,2.4),(0,10,-.3,3.65))
    box(ax,1.7,2.65,r"$\{C,I\}$",w=2,h=.6)
    box(ax,1.7,.95,r"$\{I,S\}$",w=2,h=.6)
    ax.plot([1.7,1.7],[1.25,2.35],color="black",lw=.9)
    ax.text(2.95,1.8,r"separator $\{I\}$",ha="center",va="center",fontsize=10)
    ax.text(1.7,.1,"Running intersection\nExact gluing",ha="center",va="center",fontsize=10.5)
    points=[(7.1,2.9),(5.65,1.15),(8.6,1.15)]
    for a,b in ((points[0],points[1]),(points[1],points[2]),(points[2],points[0])):
        ax.plot([a[0],b[0]],[a[1],b[1]],color="black",lw=.9,zorder=0)
    for (x,y),label in zip(points,(r"$AB$: $A=B$",r"$BC$: $B=C$",r"$AC$: $A\neq C$")):
        box(ax,x,y,label,w=2.2,h=.6,size=10.5,dashed=True)
    ax.text(7.1,.1,"Singleton marginals agree\nNo global joint law",ha="center",va="center",fontsize=10.5)
    save(fig,path)


def certificate_stack(path):
    fig,ax=canvas((6.4,3.5),(0,10,0,5.9))
    rows=[(5.3,"Finite task: boundary, poset, rational generators",.65),
          (4.2,"Producer: enumerate upsets, locate an LP optimum, rationalize",.65),
          (3.1,"Certificate: mixture, row deficits, transport, dual weights",.65),
          (1.9,"Exact upset replay; or convert to potentials\nthen exact transport replay",.85),
          (.6,"Accepted equality for this input",.65)]
    for y,label,height in rows:box(ax,5,y,label,w=9.1,h=height,size=10.5)
    for (y1,_,h1),(y2,_,h2) in zip(rows,rows[1:]):
        arrow(ax,(5,y1-h1/2),(5,y2+h2/2))
    save(fig,path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir",type=Path,default=Path(__file__).resolve().parent)
    args=parser.parse_args()
    for name,draw in (("order-context",order_context),("boolean-correlation",boolean_correlation),
                      ("dependency-scopes",dependency_scopes),("certificate-stack",certificate_stack)):
        draw(args.outdir/(name+".pdf"))
    print("Wrote four embedded-font vector schematics; label bounds checked.")


if __name__=="__main__":main()
