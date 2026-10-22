"""Build the Mathematics-only illustrated guide from a saved calculation record.
Run: .venv/bin/python scripts/build_math_guide.py --data path/to/calculations.json
Optional document packages: reportlab matplotlib numpy pypdf.
"""
from pathlib import Path
import argparse, json, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(); parser.add_argument('--data',default=str(ROOT/'docs/math-guide-example.json')); args=parser.parse_args()
a=json.loads(Path(args.data).read_text()); assert a['features']==['speed','throttle','brake','gear','rpm'] and abs(a['means'][0]-238.7721259138046)<1e-8, 'This guide narrative requires its recorded Bahrain example; adapt the narrative before using a different dataset.'; audit=a['audit']; X=np.array(audit['raw']); Z=np.array(audit['centered']); C=np.array(a['covariance']); D=np.array(a['distance']); n=len(X); p=X.shape[1]; half=len(D)
OUT=ROOT/'output/pdf/F1_Driver_DNA_Mathematics_Guide.pdf'; TMP=ROOT/'tmp/pdfs'; TMP.mkdir(parents=True,exist_ok=True); OUT.parent.mkdir(parents=True,exist_ok=True)
NAVY='#172536'; CORAL='#d84355'; CYAN='#087e90'; GRAY='#526170'; LIGHT='#edf3f6'; GOLD='#bd8200'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':NAVY,'text.color':NAVY,'axes.edgecolor':'#9ba9b3','grid.alpha':.18,'figure.facecolor':'white','savefig.facecolor':'white','axes.titleweight':'bold'})
for name,weight in [('Guide','normal'),('GuideBold','bold')]:
    pdfmetrics.registerFont(TTFont(name,font_manager.findfont(font_manager.FontProperties(family='DejaVu Sans',weight=weight))))
pdfmetrics.registerFontFamily('Guide',normal='Guide',bold='GuideBold',italic='Guide',boldItalic='GuideBold')
figs={}
def savefig(name, fig):
    path=TMP/f'{name}.png'; fig.savefig(path,dpi=190,bbox_inches='tight',pad_inches=.15); plt.close(fig); figs[name]=path

def lines(name,data,ylabel, title=None):
    fig,ax=plt.subplots(figsize=(8,3.1));
    for i,col in enumerate([CORAL,CYAN]): ax.plot(D,np.array(data)[i*half:(i+1)*half],color=col,label=['A: Leclerc L12','B: Verstappen L16'][i],lw=1.4)
    ax.set(xlabel='Aligned distance along lap (m)',ylabel=ylabel); ax.grid(); ax.legend(ncol=2,loc='upper center',bbox_to_anchor=(.5,1.2),frameon=False)
    if title: ax.set_title(title)
    savefig(name,fig)
lines('speed',X[:,0],'Speed (km/h)'); lines('zspeed',Z[:,0],'Standardised speed (no unit)')
fig,axs=plt.subplots(1,2,figsize=(8,2.7)); ds=np.array([0,10,20]); vals=np.array([100,120,110]); axs[0].plot(ds,vals,'o-',color=CYAN); axs[0].scatter([5],[110],color=CORAL,s=70,zorder=4); axs[0].set(xlabel='Distance (m)',ylabel='Speed (km/h)',title='Continuous: halfway value'); axs[1].step(ds,[3,4,4],where='post',color=CYAN); axs[1].scatter([5],[3],color=CORAL,s=70,zorder=4); axs[1].set(xlabel='Distance (m)',ylabel='Gear',title='Discrete: preceding state',yticks=[3,4]); savefig('align',fig)
fig,ax=plt.subplots(figsize=(8,3)); means=np.array(a['means']); scales=np.array(a['scales']); xx=np.linspace(100,360,200); ax.plot(xx,(xx-means[0])/scales[0],color=CYAN); ax.scatter([means[0]],[0],color=CORAL); ax.axhline(0,color=GRAY,lw=.8); ax.axvline(means[0],color=GRAY,lw=.8,ls=':'); ax.set(xlabel='Raw speed (km/h)',ylabel='Standardised speed z'); ax.text(means[0]+5,.12,'mean becomes 0'); ax.grid(); savefig('scale',fig)
fig,ax=plt.subplots(figsize=(7,3.5)); im=ax.imshow(C,cmap='RdBu_r',vmin=-np.max(np.abs(C)),vmax=np.max(np.abs(C))); names=['Speed','Throttle','Brake','Gear','RPM']; ax.set_xticks(range(p),names); ax.set_yticks(range(p),names)
for i in range(p):
 for j in range(p): ax.text(j,i,f'{C[i,j]:.3f}',ha='center',va='center',color='white' if abs(C[i,j])>.7 else NAVY,fontsize=10)
fig.colorbar(im,ax=ax,label='Covariance of standardised channels',fraction=.04); savefig('cov',fig)
Q=Z-np.array(audit['pca_center']); products=Q[:,0]*Q[:,1]
fig,ax=plt.subplots(figsize=(8,2.7)); ax.plot(np.arange(1,n+1),products,color=CYAN,lw=1); ax.axhline(0,color=GRAY,lw=.7); ax.axvline(400.5,color=CORAL,ls='--',lw=1); ax.text(130,ax.get_ylim()[1]*.82,'A rows 1-400'); ax.text(520,ax.get_ylim()[1]*.82,'B rows 401-800'); ax.set(xlabel='Joint matrix row',ylabel='q(speed) × q(throttle)'); ax.grid(); savefig('products',fig)
fig,ax=plt.subplots(figsize=(7,3.5)); ax.scatter([-1,0,1],[-2,0,2],s=55,color=CORAL,label='Centred toy observations'); v=np.array([1,2])/np.sqrt(5); w=np.array([-2,1])/np.sqrt(5)
for vec,color,label in [(v,CYAN,'v1: (1, 2) / sqrt(5)'),(w,GOLD,'v2: (-2, 1) / sqrt(5)')]: ax.arrow(0,0,*vec*1.6,color=color,width=.025,length_includes_head=True,label=label)
ax.axhline(0,color=GRAY,lw=.6); ax.axvline(0,color=GRAY,lw=.6); ax.set(xlim=(-2.3,2.3),ylim=(-2.5,2.5),xlabel='Toy channel 1',ylabel='Toy channel 2'); ax.set_aspect('equal'); ax.legend(loc='upper left',bbox_to_anchor=(1,1),frameon=False); savefig('eigentoy',fig)
fig,axs=plt.subplots(1,2,figsize=(8,2.9)); weights=np.array(a['eigenvectors'])[:,0]; axs[0].bar(names,weights,color=[CORAL if x>=0 else CYAN for x in weights]); axs[0].axhline(0,color=GRAY,lw=.8); axs[0].set(ylabel='Weight in eigenvector 1'); axs[0].tick_params(axis='x',rotation=25); axs[1].bar(range(1,p+1),a['eigenvalues'],color=CORAL); axs[1].set(xlabel='Direction number',ylabel='Eigenvalue: variance',xticks=range(1,p+1)); savefig('eigenactual',fig)
fig,ax=plt.subplots(figsize=(8,3.5));
for i,col in enumerate([CORAL,CYAN]):
 s=np.array(a['scores'][i]); ax.scatter(s[:,0],s[:,1],s=9,alpha=.55,color=col,label=['A: Leclerc L12','B: Verstappen L16'][i])
s=np.array(a['scores'][0])[80,:2]; ax.scatter(*s,s=150,facecolors='none',edgecolors=NAVY,lw=1.6); ax.annotate('A sample 81',s,xytext=(1.4,2.3),arrowprops={'arrowstyle':'->','color':NAVY}); ax.set(xlabel='PC1 score',ylabel='PC2 score'); ax.grid(); ax.legend(frameon=False); savefig('pca',fig)
terms=np.array(audit['pca_contributions'])[80,0]; fig,ax=plt.subplots(figsize=(8,2.7)); ax.bar(names,terms,color=CORAL); ax.set(ylabel='Contribution to PC1 score'); ax.axhline(0,color=GRAY,lw=.8); ax.set_title(f'Sum of bars = {sum(terms):.5f}'); savefig('terms',fig)
fig,ax=plt.subplots(figsize=(8,2.8)); ev=100*np.array(a['explained_variance']); ax.bar(range(1,p+1),ev,color=CYAN,label='Individual component'); ax.plot(range(1,p+1),np.cumsum(ev),'o-',color=CORAL,label='Cumulative'); ax.set(xlabel='Principal component',ylabel='Explained variation (%)',xticks=range(1,p+1),ylim=(0,108)); ax.legend(frameon=False); ax.grid(axis='y'); savefig('variance',fig)
fig,axs=plt.subplots(1,3,figsize=(8,2.7)); toy=np.array([[1,1],[2,2]]); matrices=[np.array([[1/np.sqrt(5)],[2/np.sqrt(5)]]),np.array([[np.sqrt(10)]]),np.array([[1/np.sqrt(2),1/np.sqrt(2)]])]
for ax,m,title in zip(axs,matrices,['U: row amounts','Sigma: strength','V transpose: recipe']):
 ax.imshow(m,cmap='Blues',vmin=0,vmax=3.2); ax.set_title(title,fontsize=10); ax.axis('off')
 for (i,j),v in np.ndenumerate(m): ax.text(j,i,f'{v:.5f}',ha='center',va='center',fontsize=12,color='white' if v>2 else NAVY)
savefig('svdtoy',fig)
fig,axs=plt.subplots(1,2,figsize=(8,2.7)); sv=np.array(a['singular_values']); axs[0].bar(range(1,p+1),sv,color=CYAN); axs[0].set(xlabel='Singular component',ylabel='Singular value',xticks=range(1,p+1)); axs[1].plot(range(1,p+1),sv**2/(n-1),'o-',color=CORAL,label='sigma squared / 799'); axs[1].scatter(range(1,p+1),a['eigenvalues'],marker='x',color=NAVY,s=65,label='Covariance eigenvalue'); axs[1].set(xlabel='Component',ylabel='Variance',xticks=range(1,p+1)); axs[1].legend(frameon=False,fontsize=8); savefig('svdbridge',fig)
fig,axs=plt.subplots(2,1,figsize=(8,4),sharex=True)
for ax,r in zip(axs,[1,2]):
 rec=np.array(audit['ranks'][r-1]['reconstructed']); ax.plot(D,X[:half,0],color=CORAL,lw=1,label='A aligned speed'); ax.plot(D,rec[:half,0],color=CYAN,lw=1.3,ls='--',label=f'Rank {r} reconstruction'); ax.set_ylabel('Speed (km/h)'); ax.grid(); ax.legend(frameon=False,ncol=2,fontsize=9)
axs[-1].set_xlabel('Aligned distance (m)'); savefig('ranktraces',fig)
fig,axs=plt.subplots(1,2,figsize=(8,2.8)); ranks=audit['ranks']; rr=[t['rank'] for t in ranks]; axs[0].plot(rr,[t['relative_error'] for t in ranks],'o-',color=CYAN); axs[0].set(xlabel='Components kept',ylabel='Relative matrix error',xticks=rr); axs[1].plot(rr,[100*t['retained_energy'] for t in ranks],'o-',color=CORAL); axs[1].set(xlabel='Components kept',ylabel='Retained variation (%)',xticks=rr); savefig('rankerrors',fig)
fig,ax=plt.subplots(figsize=(8,2.8)); u=np.linspace(0,1,150)
for degree,col in [(1,CYAN),(2,CORAL),(3,GOLD)]: ax.plot(u,100+40*u**degree,label=f'100 + 40u^{degree}',color=col)
ax.set(xlabel='Normalised distance u (no unit)',ylabel='Toy fitted speed (km/h)'); ax.legend(frameon=False); ax.grid(); savefig('polys',fig)
fig,axs=plt.subplots(2,1,figsize=(8,4),sharex=True)
for i,col in enumerate([CORAL,CYAN]):
 fit=a['fit']['drivers'][i]; ax=axs[i]; ax.plot(a['fit']['distance'],fit['observed'],color=col,lw=1,label=['A observed','B observed'][i]); ax.plot(a['fit']['distance'],fit['fitted'],color=NAVY,lw=1.5,ls='--',label='Degree 3 fit'); ax.set_ylabel('Speed (km/h)'); ax.grid(); ax.legend(frameon=False,ncol=2,fontsize=9)
axs[-1].set_xlabel('Aligned distance (m)'); savefig('fit',fig)
fig,ax=plt.subplots(figsize=(8,3));
for i,col in enumerate([CORAL,CYAN]):
 f=a['fit']['drivers'][i]; ax.plot(a['fit']['distance'],np.array(f['observed'])-f['fitted'],color=col,lw=1,label=['A: Leclerc','B: Verstappen'][i])
ax.axhline(0,color=NAVY,lw=.7); ax.set(xlabel='Aligned distance (m)',ylabel='Residual = observed - fitted (km/h)'); ax.legend(ncol=2,frameon=False); ax.grid(); savefig('residuals',fig)

W,H=A4; M=46; CW=W-2*M
c=canvas.Canvas(str(OUT),pagesize=A4); c.setTitle('F1 Driver DNA - Mathematics, From First Steps to Teaching It'); c.setAuthor('F1 Driver DNA project'); c.setSubject('Illustrated beginner workbook for the actual Mathematics module, with recorded calculations and worked examples')
styles={
 'p':ParagraphStyle('p',fontName='Guide',fontSize=10.5,leading=15.3,textColor=colors.HexColor(NAVY),spaceAfter=8),
 'small':ParagraphStyle('small',fontName='Guide',fontSize=8.5,leading=12,textColor=colors.HexColor(GRAY)),
 'h':ParagraphStyle('h',fontName='GuideBold',fontSize=12.6,leading=17,textColor=colors.HexColor(NAVY)),
 'box':ParagraphStyle('box',fontName='Guide',fontSize=10.3,leading=15,textColor=colors.HexColor(NAVY)),
 'cell':ParagraphStyle('cell',fontName='Guide',fontSize=9,leading=12.6,textColor=colors.HexColor(NAVY)),
 'headcell':ParagraphStyle('headcell',fontName='GuideBold',fontSize=9,leading=12.6,textColor=colors.white),
}
page_no=0; y=0; pages=[]; overflows={}
def para(text,style='p',width=CW):
 return Paragraph(text,styles[style])
def check():
 if y<58: overflows[page_no]=round(y,1)
def page(title,section='LEARN THE MATHEMATICS'):
 global y,page_no
 if page_no: check(); c.showPage()
 page_no+=1; pages.append(title)
 c.setFillColor(colors.HexColor(NAVY)); c.rect(0,H-12,W,12,fill=1,stroke=0)
 c.setFillColor(colors.HexColor(CORAL)); c.rect(M,H-45,26,3,fill=1,stroke=0)
 c.setFillColor(colors.HexColor(GRAY)); c.setFont('GuideBold',8); c.drawString(M+35,H-46,'F1 DRIVER DNA  /  MATHEMATICS ONLY')
 c.setFont('Guide',8); c.drawRightString(W-M,31,f'{page_no:02d}')
 c.setStrokeColor(colors.HexColor('#d4dfe6')); c.line(M,47,W-M,47)
 c.setFillColor(colors.HexColor(GRAY)); c.drawString(M,31,'From first steps to explaining it yourself')
 c.bookmarkPage(f'p{page_no}'); c.addOutlineEntry(title,f'p{page_no}',level=0,closed=False)
 c.setFillColor(colors.HexColor(CYAN)); c.setFont('GuideBold',8.3); c.drawString(M,H-72,section.upper())
 title_p=Paragraph(title,ParagraphStyle('title',fontName='GuideBold',fontSize=23,leading=28,textColor=colors.HexColor(NAVY)))
 _,hh=title_p.wrap(CW,100); title_p.drawOn(c,M,H-90-hh); y=H-105-hh

def p_(text):
 global y
 ob=para(text); _,hh=ob.wrap(CW,1000); ob.drawOn(c,M,y-hh); y-=hh+8; check()
def h(text):
 global y
 ob=para(text,'h'); _,hh=ob.wrap(CW,1000); ob.drawOn(c,M,y-hh); y-=hh+7; check()
def box(label,text):
 global y
 ob=para(f'<b>{label}</b><br/>{text}','box',CW-24); _,hh=ob.wrap(CW-24,1000); height=hh+22
 c.setFillColor(colors.HexColor(LIGHT)); c.roundRect(M,y-height,CW,height,6,fill=1,stroke=0); c.setFillColor(colors.HexColor(CYAN)); c.rect(M,y-height,3,height,fill=1,stroke=0); ob.drawOn(c,M+12,y-11-hh); y-=height+12; check()
def table(headers,rows,widths=None):
 global y
 data=[[para(str(x),'headcell') for x in headers]]+[[para(str(x),'cell') for x in r] for r in rows]
 t=Table(data,colWidths=widths or [CW/len(headers)]*len(headers),hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(NAVY)),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor(LIGHT)]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#cbd5de'))]))
 _,hh=t.wrap(CW,1000); t.drawOn(c,M,y-hh); y-=hh+12; check()
def fig(name,caption,maxh=225):
 global y
 ir=ImageReader(str(figs[name])); iw,ih=ir.getSize(); ww=CW; hh=ww*ih/iw
 if hh>maxh: hh=maxh; ww=hh*iw/ih
 c.drawImage(ir,M+(CW-ww)/2,y-hh,width=ww,height=hh,mask='auto'); y-=hh+6
 ob=para(caption,'small'); _,ht=ob.wrap(CW,1000); ob.drawOn(c,M,y-ht); y-=ht+13; check()
def eq(text): box('READ THE EQUATION',text)
def ask(text): box('SAY IT BACK',text)

page('Mathematics you can see, understand and teach','An illustrated learning guide')
p_('Start with a simple question: <b>How can two laps, each with hundreds of numbers, become understandable pictures?</b> This workbook takes you from counting and averages to PCA, eigenvectors, SVD and curve fitting, one small step at a time.')
fig('pca','A real output from this project: each dot is one aligned distance sample from one of two selected laps.',235)
box('YOU DO NOT NEED ADVANCED MATH TO BEGIN','Read the everyday explanation first. Then try the small practice example. Finally, match it to the real app. Symbols are introduced before they are used.')
p_('<b>Scope:</b> only the current Mathematics module: its inputs, seven walkthrough stages, advanced tabs, graphs, controls, inspector and calculation exports. This is not a guide to race replay, sound, driver cards or the rest of the website.')
p_('<b>Recorded example:</b> 2024 Bahrain Qualifying. Driver A: Charles Leclerc, lap 12. Driver B: Max Verstappen, lap 16. Results belong to these selected measurements, not every race or every driver.')
p_('Edition: 22 October 2026. Read in short sessions. A grown-up can help with the longer words; the ideas are explained from the beginning.')

page('Your learning route','How to use this workbook')
p_('You do not have to learn everything in one sitting. First understand the story. Then follow one actual number through the calculations. Finally, explain the story without looking.')
table(['Read these pages','What you will be able to explain'],[
('3-8: The ingredients','The pipeline, symbols, channels, alignment and the measurement matrix.'),
('9-12: Make fair comparisons','Mean, spread, standardisation and the scaling switch.'),
('13-16: Find patterns','Covariance, eigenvalues, eigenvectors and their checks.'),
('17-20: Draw the pattern','PCA, the scatter plot, one point and explained variation.'),
('21-25: Take apart and rebuild','SVD, its matrices, rank and reconstruction error.'),
('26-30: Draw a smooth summary','Polynomials, normalised distance, least squares, residuals, RMSE and R².'),
('31-35: Use and audit the app','Controls, inspector, advanced tabs, exports and backend steps.'),
('36-44: Practise and teach','Mistakes, experiments, quiz, answers, teach-back and reference pages.')],[155,CW-155])
box('THREE LABELS YOU WILL SEE','<b>Practice example:</b> small invented numbers for learning. <b>Recorded example:</b> numbers from the saved calculation of the two F1 laps. <b>Say it back:</b> a short question to test understanding.')
p_('All printed numbers are rounded. Small last-digit differences are normal when you calculate using rounded values. The JSON export keeps the returned numerical precision. PDF bookmarks let you jump to any page.')

page('The whole story in one picture','The map before the details')
box('MAIN PATH','Two selected laps → shared distance grid → measurement table X → transformed table Z → covariance C → eigenvectors and PCA scores. The same Z also goes directly to SVD and reconstruction.')
box('SEPARATE PATH','Aligned <b>speed</b> + selected distance interval → polynomial fit → fitted speed + residuals + RMSE + R². Curve fitting does not wait for PCA or use its scores.')
table(['Stage','Simple question','Visible output'],[
('Measurements','What was measured at the same places?','Aligned traces and X table'),('Standardise','How far from usual is each value?','Z traces, mean and scale'),('Covariance','Which channels vary together?','Products graph and C matrix'),('Eigenvectors','Which pattern directions matter?','Weights, eigenvalues, equation check'),('PCA projection','Where does each observation sit?','PC1/PC2 dots and contribution bars'),('SVD reconstruction','Can fewer patterns rebuild it?','Reconstructed traces and error curve'),('Curve fitting','Can a smooth curve summarise speed?','Observed/fitted traces and residuals')],[92,195,CW-287])
p_('Think of a box of building blocks. X is the box as collected. Z puts the blocks on comparable scales. PCA finds useful ways to look at the arrangement. SVD describes how to take it apart and rebuild it. Curve fitting makes a separate smooth sketch of speed.')
ask('Point to the branch that fits speed. Does it use PCA? Answer: no, it starts from aligned speed directly.')

page('Small maths tools you already know','Foundation 1 / arithmetic')
table(['Tool','Plain meaning','Practice example'],[('Add / sum','Put amounts together.','2 + 3 + 4 = 9'),('Subtract','Find a difference.','12 - 10 = 2'),('Multiply','Scale or repeat an amount.','3 × 4 = 12'),('Divide','Share an amount equally.','12 / 3 = 4'),('Square','Multiply a number by itself.','(-3)² = 9'),('Square root','Find a non-negative number whose square gives this amount.','sqrt(9) = 3'),('Percentage','An amount out of 100.','0.25 = 25%')],[93,240,CW-333])
h('Negative does not mean wrong')
p_('If the usual speed is 100 and you measure 90, the difference is -10. It simply means 10 below the usual value. Later, a negative PCA score means a position on one side of a direction, not a bad driver.')
h('Why squares appear so often')
p_('Suppose two errors are +3 and -3. Their ordinary sum is 0 even though both are mistakes. Squaring gives 9 + 9 = 18, so they cannot cancel. This is why variance, least squares and RMSE use squares.')
box('TINY PRACTICE','Errors are +2 and -4. Squares are 4 and 16. Their mean square is (4 + 16) / 2 = 10. The square root is about 3.162. You have already performed the core idea of RMSE!')

page('Read symbols like little name tags','Foundation 2 / mathematical language')
p_('An equation is a sentence about numbers. A letter is a reusable name for a number or a collection of numbers. A small number below a letter is an address, not a multiplication.')
table(['Symbol / name','How to read it','Meaning in this guide'],[('xᵢⱼ / x i j','x at row i, column j','One aligned measurement'),('n and p','n rows, p channels','Normally n = 800; p = 2 to 5'),('i, j, k, r','row, channel, component, rank','Counters or choices, not extra data'),('Σ / summation','Add the listed terms','Σ over j means add across channels'),('μ / mu','mew','Mean of a channel'),('s','scale','Population standard deviation when scaling is on'),('λ / lambda','lam-da','An eigenvalue: variance along a direction'),('σ / sigma','sig-ma','A singular value: component strength'),('^ / power','raised to','u^2 means u × u'),('hat, as in x̂','x hat','A reconstructed or fitted value'),('T, as in Xᵀ','transpose','Swap matrix rows and columns'),('||A|| / norm','size of A','A defined measure of total magnitude')],[112,135,CW-247])
box('TWO JOBS FOR SIGMA','A summation sign Σ means “add”. The capital matrix name Σ in SVD means a diagonal table of singular values. Context tells you which one it is. Lowercase σ is one singular value.')
p_('A vector is a list of numbers. A matrix is a rectangular table of numbers. The next pages make both concrete. “Real numbers”, written ℝ, include everyday whole numbers, fractions and decimals.')

page('Meet the five channels','Measurements / what each column means')
table(['Channel','Meaning and unit','Why include it?'],[('Speed','How fast the car travels; km/h.','Shows acceleration and slow corners.'),('Throttle','Reported throttle opening; percent (%).','Shows when power is requested. It is not engine power itself.'),('Brake','Reported brake state: 0 off, 1 on.','Marks braking activity. It is not brake pressure or braking force.'),('Gear','Reported gear number.','Shows the selected transmission state; not a continuous speed.'),('RPM','Engine revolutions per minute.','Shows engine rotation rate; affected by gear and throttle.')],[84,235,CW-319])
p_('A <b>feature</b> is a selected channel used as one mathematical input column. You can choose two to five features. Distance identifies a place on the lap; elapsed time identifies when that driver reached it. They are not PCA feature columns in this module.')
box('A SAMPLE IS A SNAPSHOT','An observation can be a row such as: speed 270, throttle 99, brake 0, gear 7, RPM 10800. These are five descriptions of the same moment/place, not five separate drivers.')
h('A shared model')
p_('Both laps help choose one common mean, one scale and one set of directions. If each driver got a different set of axes, comparing their dots would be like comparing two maps with different rulers.')
ask('Why is RPM not the same as speed? A car can use a different gear at the same road speed, so the engine can turn at a different rate.')

page('Put both drivers at the same places','Measurements / distance alignment')
p_('Imagine two children taking photos while walking. One takes 7 photos and the other takes 10. Photo number 4 will not necessarily show the same place. We need shared places before comparing their measurements.')
p_('The backend sorts each lap by distance, removes duplicate distances and drops rows missing required finite values. It finds the distance range recorded by both laps, then chooses <b>400 evenly spaced distances</b> in that overlap.')
fig('align','Practice example, not F1 data. At 5 m, speed is interpolated to 110 km/h; gear stays at the preceding recorded value 3.',190)
eq('Continuous interpolation: value = left value + fraction × (right value - left value).<br/>At 5 m between 0 and 10 m: fraction = 5 / 10 = 0.5; speed = 100 + 0.5 × (120 - 100) = 110.')
p_('Speed, throttle, RPM and elapsed time use straight-line interpolation between recorded neighbours. Brake and gear use the preceding sample, so the app does not create gear 3.5 or a half-on brake state.')
box('WHAT ALIGNMENT CAN AND CANNOT DO','It makes locations comparable. It cannot create new sensor information. The recorded example has 687 + 700 source samples and becomes 400 + 400 aligned observations. Nearby rows are related, not 800 independent experiments.')

page('X: the big table of measurements','Measurements / matrices and addresses')
fig('speed','Recorded example. Same x-axis distances for both laps. A low point shows a slow part of the selected lap; it does not by itself identify a turn.',190)
p_('The letter <b>X</b> names the table of selected raw aligned channels. “Raw” here means before mathematical centring/scaling; it has already been aligned. Driver A supplies the first 400 rows. Driver B supplies the next 400 rows.')
table(['Address','What it refers to'],[('X has shape 800 × 5','800 rows and 5 selected feature columns.'),('Row 81','Driver A, aligned sample 81 (zero-based index 80).'),('Row 481','Driver B, aligned sample 81 (zero-based index 480).'),('x[81, speed] ≈ 268.74765','A speed measurement in km/h at 1075.96431 m.'),('A row vector','All selected feature values for one observation.'),('A column vector','One channel across all observations.')],[168,CW-168])
eq('Joint row = driver offset + sample number.<br/>A offset = 0; B offset = 400. B sample 81 therefore lives at row 400 + 81 = 481.')
ask('What happens to X if you choose only Speed and Throttle? It becomes 800 × 2. Rows stay observations; columns become those two features.')

page('Mean: find the shared middle','Standardise / subtract the average')
p_('The <b>mean</b> is the total shared equally. If three children have 80, 100 and 120 marbles, they have 300 altogether. Sharing equally gives 100 each. Their mean is 100.')
eq('Mean of channel j: μⱼ = (x₁ⱼ + x₂ⱼ + ... + xₙⱼ) / n.<br/>Centred value = original value - mean.')
table(['Practice speed','Subtract mean 100','Centred speed'],[('80','80 - 100','-20'),('100','100 - 100','0'),('120','120 - 100','+20')])
p_('Centring moves the shared middle to zero. It does not change the gap between any two values: 120 - 80 is 40, and 20 - (-20) is still 40. This makes “above usual” and “below usual” easy to see.')
box('RECORDED EXAMPLE','Using both laps together, the speed mean is 238.77213 km/h. At A sample 81, speed is 268.74765 km/h. Its centred difference is 268.74765 - 238.77213 = 29.97552 km/h.')
h('Why one mean per channel?')
p_('Adding speed to RPM would mix different kinds of measurements. The app therefore finds a separate middle for speed, throttle, brake, gear and RPM. Each middle uses all 800 values in that selected column.')
ask('If a centred value is -12, what does it say? The measurement is 12 original units below that channel’s shared mean.')

page('Standard deviation: a ruler for spread','Standardise / understand s')
p_('Two classes can have the same average height but very different spreads. <b>Variance</b> measures average squared distance from the mean. <b>Standard deviation</b> takes a square root so the ruler returns to the original units.')
eq('Population variance = Σᵢ (xᵢ - μ)² / n.<br/>Standard deviation s = sqrt(population variance).<br/>The app’s StandardScaler uses this n denominator (ddof = 0).')
table(['Practice speeds','80','100','120'],[('Difference from μ = 100','-20','0','20'),('Squared difference','400','0','400')],[173,110,110,CW-393])
p_('Add squares: 400 + 0 + 400 = 800. Divide by 3: 266.66667. Take the square root: s ≈ 16.32993 km/h. A difference of 20 km/h is about 20 / 16.32993 = <b>1.22474 spread-rulers</b>.')
box('RECORDED EXAMPLE','Speed has mean 238.77213 km/h and scale 59.82663 km/h. RPM has mean 10723.81212 RPM and scale 1119.29203 RPM. Each channel gets its own ruler.')
h('Why divide by n here but n - 1 later?')
p_('Once the mean is subtracted, the deviations must add to zero. For example, if two deviations are -20 and 0, the third must be +20. Only n - 1 deviations can vary freely. Sample covariance uses the n - 1 convention. StandardScaler instead describes the full input column using n. “ddof” means the count subtracted from n in the denominator.')
ask('Why take the square root? So a speed spread can be understood in km/h instead of squared km/h.')

page('Z: describe values on fair rulers','Standardise / one worked calculation')
eq('zᵢⱼ = (xᵢⱼ - μⱼ) / sⱼ.<br/>Read: subtract this channel’s mean, then divide by this channel’s spread.')
fig('scale','Recorded speed mean and scale. The same speed can be described in km/h or in standard-deviation units.',190)
p_('If z = 0, the measurement is at the shared mean. If z = 1, it is one standard deviation above that mean. If z = -2, it is two standard deviations below. Z is the whole table of these transformed values.')
box('RECORDED A SAMPLE 81','x = 268.74765 km/h; μ = 238.77213 km/h; s = 59.82663 km/h.<br/>z = (268.74765 - 238.77213) / 59.82663 ≈ <b>0.50104</b>.<br/>The km/h units cancel. This observation is about half a spread-ruler above the mean.')
p_('Why do this? A raw RPM number near 11000 is much larger numerically than a brake value of 0 or 1. Standardising stops unit size alone from deciding which channel dominates. It does not prove all channels are equally informative.')
ask('Can you recover the original value? Yes: x = z × s + μ. This reverse step is used after SVD reconstruction to show speeds in km/h again.')

page('What the scaling switch really changes','Standardise / on versus off')
fig('zspeed','Recorded standardised speed. Its shape matches the speed trace, but the shared mean is now near zero.',135)
table(['Standardize channels ON','Standardize channels OFF'],[('Subtract each mean and divide by its standard deviation.','Subtract each mean; use scale 1.'),('z = (x - μ) / s','z = x - μ'),('Feature numbers become unitless.','Each column keeps its original measurement units.'),('Variation is balanced against each channel’s own spread.','Large numerical units, especially RPM, can dominate.')])
p_('Turning scaling off does <b>not</b> mean leaving the data unchanged: centring still happens. You must press Calculate after changing this top-level option. Choosing new features also recomputes the model.')
box('A SMALL BUT IMPORTANT DETAIL','If a selected channel is constant, its spread is zero. The scaler uses an effective scale of 1, and its centred column becomes all zeros. If every selected channel has no variation, analysis is rejected rather than inventing directions.')
p_('After centring, a computer can leave tiny means such as 0.000000000000001 because decimal arithmetic is finite. For covariance and PCA, the code subtracts that remaining mean. We call the result <b>Q = Z - mean(Z)</b>. Q and Z are almost identical here.')
ask('Will an unscaled RPM loading tell you that engine speed is the most important cause? No. Numerical scale can make it look dominant; covariance and PCA do not establish causes.')

page('Covariance: do two channels move together?','Covariance / first use tiny numbers')
p_('Imagine three observations. The centred values of channel 1 are -1, 0, 1. Channel 2 values are -2, 0, 2. When one is below its mean, the other is below too. When one is above, the other is above too.')
table(['Row','q for channel 1','q for channel 2','Product'],[('1','-1','-2','2'),('2','0','0','0'),('3','1','2','2')])
eq('C[j,k] = Σᵢ qᵢⱼ × qᵢₖ / (n - 1).<br/>Practice cross-covariance = (2 + 0 + 2) / (3 - 1) = 2.')
p_('A positive product means both values are on the same side of their means. A negative product means opposite sides. Add all row products, then divide by n - 1. One product is one contribution, not the whole covariance.')
table(['Covariance sign','Plain interpretation'],[('Positive','The channels tend to vary in the same direction.'),('Negative','They tend to vary in opposite directions.'),('Near zero','Little linear co-variation; a curved relationship can still exist.')],[130,CW-130])
p_('Pair every channel with every channel to build a square covariance matrix. A diagonal cell pairs a channel with itself: it is that channel’s variance. C[j,k] = C[k,j], so the matrix mirrors across its diagonal.')
ask('What is the full covariance matrix for this practice example? C = [[1, 2], [2, 4]]. Try the two diagonal calculations yourself.')

page('Read the covariance graphs in your app','Covariance / recorded results')
fig('cov','Recorded 5 × 5 covariance matrix. Values and colour strength describe magnitude; positive and negative use opposite colour families.',190)
fig('products','Recorded speed/throttle products. The horizontal axis is joint row number, not metres or seconds.',150)
p_('Click a covariance cell to choose a pair. The products graph then shows the 800 terms used for that cell. At the A/B boundary, the line joins different laps; that join is an ordering choice, not a physical jump while driving.')
box('ONE REAL CELL','Standardised speed/throttle covariance ≈ <b>0.50639</b>. Add all 800 speed/throttle products and divide by 799. A single large positive term cannot establish the final sign by itself.')
p_('With non-constant standardised columns, each diagonal is approximately 800 / 799 = 1.00125, not exactly 1. The scale used n, while covariance uses n - 1. This covariance is close to, but not exactly, a correlation matrix. Unscaled covariance has products of original units.')

page('Eigenvectors: directions that stay directions','Eigenvectors / a picture with two channels')
p_('A matrix can act like a machine that moves an arrow. Most arrows turn. An <b>eigenvector</b> is a special non-zero arrow whose line stays the same under that machine. An <b>eigenvalue</b> tells how much it is stretched.')
fig('eigentoy','Practice example. The observations lie along v1. The perpendicular direction v2 contains no spread.',195)
eq('C v = λ v.<br/>C = covariance machine; v = direction; λ = stretch factor.<br/>For a covariance matrix, that λ is the variance along a unit direction v.')
p_('Use the practice C = [[1, 2], [2, 4]]. The arrow (1, 2) becomes (5, 10): first output = 1×1 + 2×2 = 5; second = 2×1 + 4×2 = 10. This is 5 × (1, 2), so λ = 5.')
p_('The arrow (-2, 1) becomes (0, 0), so its λ is 0. The app uses <b>unit vectors</b>, length 1: v1 = (1, 2) / sqrt(5). Dividing by the length keeps direction while making a fair ruler for variance.')
ask('Is an eigenvector a driver? No. Its entries are weights for selected channels. It is a direction in measurement space.')

page('Eigenvalues and weights in five dimensions','Eigenvectors / the actual output')
fig('eigenactual','Recorded results. Left: the first eigenvector has one weight per selected channel. Right: variance along each ordered eigenvector.',180)
p_('We cannot draw a five-dimensional arrow on paper, so the app shows its five entries as bars. The bar height is a <b>weight</b>, not the amount of that channel in km/h or RPM. The eigenvalue chart orders directions from greatest to least variance.')
table(['Direction','Eigenvalue λ','Meaning'],[(str(i+1),f'{v:.5f}', 'Largest spread' if i==0 else 'Successively smaller spread') for i,v in enumerate(a['eigenvalues'])],[85,115,CW-200])
p_('The table labelled Cv and λv shows the two ways to calculate the same output vector. The residual norm ||Cv - λv||₂ asks how far apart they are. The first recorded residual is about 1.35 × 10^-15: essentially zero at numerical precision.')
box('SIGNS CAN FLIP','v and -v describe the same line. If a component reverses signs, its scores can reverse too while distances and reconstruction stay equivalent. With exactly equal eigenvalues, different valid bases can describe the same subspace. Do not grade a driver from the sign of a weight.')

page('PCA: choose a better view of the cloud','PCA / from arrows to coordinates')
p_('<b>PCA</b> means Principal Component Analysis. “Principal” means main. “Component” means a new combined direction. PCA chooses perpendicular directions that capture as much remaining variation as possible.')
h('Imagine turning a camera')
p_('A long thin line of toy cars might look crowded from one angle and spread out from another. Turning the view does not move the cars. PCA changes the coordinate directions used to describe the observations. For more than two channels, it also lets us keep just a few directions for a picture.')
eq('For observation i and component k:<br/>tᵢₖ = Σⱼ qᵢⱼ × wₖⱼ.<br/>Read: multiply each centred feature by its component weight, then add.')
table(['Name','Job'],[('Q','The transformed input after the tiny remaining mean is removed.'),('w[k,j] / loading','Weight of channel j in PCA component k.'),('t[i,k] / score','Position of observation i along component k.'),('PC1','Direction capturing the greatest variance.'),('PC2','Next direction, perpendicular to PC1, capturing the greatest remaining variance.')],[135,CW-135])
p_('The multiplication-and-addition is a <b>dot product</b>, also called projection onto a unit direction. A loading belongs to a channel and a component. A score belongs to an observation and a component. Confusing these two is a common mistake.')
ask('What does PCA learn from here? One jointly transformed table of the two selected laps. The same directions are then used for both drivers.')

page('Read the PCA scatter plot','PCA / every dot has an address')
fig('pca','Recorded example. Coral is A and cyan is B. The ring marks A aligned sample 81. Each axis is a component score, not time or speed.',235)
p_('A dot represents <b>one aligned distance sample from one driver</b>. Its horizontal coordinate is PC1 score; its vertical coordinate is PC2 score. The full chart has 400 dots per driver. Hover to see scores and distance; click a dot to inspect its row.')
box('HOW TO READ A SHAPE','Nearby dots have similar coordinates on these two component directions. They may still differ on components 3-5. Overlap suggests similar selected measurements in this view; it does not establish equal skill, personality or lap time.')
p_('The cloud can mix straights, braking and corner exits because these places can have different channel combinations. Distance in the tooltip tells you where an observation came from. A point far left is not automatically “slow” or “bad”: inspect the loadings first.')
p_('The Walkthrough component selector changes the inspected score and contribution bars. The scatter axes remain <b>PC1 and PC2</b>. Selecting PC3 does not turn that scatter into a PC1-versus-PC3 plot.')
ask('Why can two dots at different distances overlap? They can have similar combinations of the chosen channels even though the car was at different places.')

page('Build one real PCA point by hand','PCA / follow A sample 81')
p_('Choose A / Leclerc, sample 81, component PC1. This is joint row 81 at 1075.96431 m. The inspector shows the input, standardisation and every contribution used for this score.')
table(['Channel','q (rounded)','PC1 weight','Product'],[(names[j],f'{Q[80,j]:.5f}',f'{a["components"][0][j]:.5f}',f'{terms[j]:.5f}') for j in range(p)],[90,110,130,CW-330])
eq(f'PC1 score = sum of the five products ≈ <b>{sum(terms):.5f}</b>.<br/>Speed term: 0.50104 × 0.51187 ≈ 0.25647.')
fig('terms','Recorded channel contributions for this single point. Add signed bar heights; do not add only their absolute values.',175)
p_('The brake value is below its mean, so its q is negative. The PC1 brake weight is also negative. Negative × negative makes a positive contribution. A positive bar is a contribution to this coordinate, not a “good driving” mark.')
ask('Explain the difference: the loading is the recipe weight, the q value is this row’s ingredient amount, and the product is this row’s contribution. Adding the contributions gives the score.')

page('Explained variance: how much view is kept?','PCA / percentages without misleading claims')
eq('Explained variance ratio for component k = λₖ / Σⱼ λⱼ.<br/>Multiply the ratio by 100 to display a percentage.')
fig('variance','Recorded individual and cumulative explained variation. The first two components together retain about 88.73% of the selected transformed variation.',215)
p_('In this example PC1 explains 60.85871% and PC2 explains 27.86951%. Together that is <b>88.72822%</b>. The other three components contain the remaining 11.27178%. The plot shows a two-dimensional view of a five-feature table.')
box('WHAT 88.73% DOES NOT MEAN','It is not 88.73% driver skill, 88.73% prediction accuracy or 88.73% of the lap distance. It is the share of variance represented by these component directions in this specific transformed dataset.')
p_('Why keep fewer directions? To show a readable picture or a compact approximation. Why keep more? To preserve more detail. Small-variance directions can still contain useful differences; PCA ranks by variance, not by what a human considers most important.')
ask('If PC1 explains 70% and PC2 explains 20% in a practice dataset, what is kept by the 2D view? 90%, with 10% outside those two directions.')

page('SVD: take the table apart and rebuild it','SVD / three cooperating pieces')
p_('<b>SVD</b> means Singular Value Decomposition. “Decomposition” means taking something into pieces that multiply back together. It is like describing music using pattern recipes, their strengths and how much each observation uses each recipe.')
eq('Z = U Σ Vᵀ.<br/>Here Z is the centred and optionally standardised table, not raw X.')
table(['Piece','Plain job','Shape here'],[('U','How much each observation uses each singular pattern, before multiplying by its strength.','800 × 5'),('Σ (capital sigma)','Diagonal table of strengths. Only diagonal entries are non-zero.','5 × 5'),('Vᵀ (V transpose)','One feature recipe per row; right singular directions.','5 × 5')],[75,310,CW-385])
p_('A matrix product is a systematic multiply-and-add. For one reconstructed entry, multiply a row amount, the matching strength and the matching channel weight; then add across components. U on its own is not the PCA score table. The strengths must be included.')
box('WHY THIS CONNECTS TO PCA','For the centred data, the right singular directions describe the same variance directions as PCA, up to possible sign choices (or basis choices for ties). Multiplying U by Σ gives coordinates in those directions. The app’s separately computed PCA also removes the tiny remaining mean of Z.')
p_('“Thin SVD” keeps only the needed columns of U. It does not create an 800 × 800 U table here. The SVD factorisation uses all selected feature columns of the joint matrix.')
ask('Which piece knows the channel recipes? Vᵀ. Which piece contains the component strengths? Σ.')

page('A whole SVD you can multiply yourself','SVD / exact small practice example')
p_('<b>Practice example only:</b> use a simple table A = [[1, 1], [2, 2]]. This standalone matrix is for learning multiplication; it is not the project’s centred telemetry matrix. Its second column repeats the first, so one pattern is enough.')
fig('svdtoy','A compact rank-1 SVD for the practice matrix. Values shown are rounded; exact expressions below reconstruct it exactly.',150)
eq('U = [[1 / sqrt(5)], [2 / sqrt(5)]]<br/>Σ = [[sqrt(10)]]<br/>Vᵀ = [[1 / sqrt(2), 1 / sqrt(2)]].')
h('Rebuild the first entry')
p_('(1 / sqrt(5)) × sqrt(10) × (1 / sqrt(2)) = 1. The second entry uses the same channel recipe weight, so it is also 1. The second row uses 2 / sqrt(5), giving entries 2 and 2.')
h('Why only one pattern?')
p_('The feature recipe says “use both columns equally”. The second row uses twice as much of it. Nothing remains that needs another non-zero pattern. This matrix has <b>rank 1</b>: one independent direction is sufficient.')
box('A USEFUL DISTINCTION','Multiplying all pieces back is an identity check. Keeping only some non-zero pieces for a larger matrix is an approximation. Neither operation predicts the next lap.')
ask('What if the second column changed independently of the first? One recipe might no longer be enough. A second independent pattern could be needed.')

page('Connect singular values to eigenvalues','SVD / the same pattern seen two ways')
fig('svdbridge','Recorded values. The two markers on the right overlap because sigma squared / 799 matches the covariance eigenvalue to numerical precision.',135)
table(['Component','Singular value σ','σ² / 799 ≈ λ'],[(str(i+1),f'{v:.5f}',f'{v*v/(n-1):.5f}') for i,v in enumerate(a['singular_values'])])
eq('If Q = Z exactly: C = ZᵀZ / (n - 1).<br/>With Z = UΣVᵀ, this gives C = VΣ²Vᵀ / (n - 1).<br/>Therefore λₖ = σₖ² / (n - 1).')
p_('The middle fact is that U’s singular columns are perpendicular and length 1, so UᵀU is the identity. In this app, covariance and PCA subtract a tiny residual mean while SVD uses Z directly, so the connection holds to numerical precision.')
box('ORTHOGONALITY CHECK','Perpendicular unit directions multiply with their transpose to give the identity matrix I: ones on its diagonal, zeros elsewhere. The app checks ||VᵀV - I||F. The recorded result is about 1.04 × 10^-15, which is very close to zero.')
p_('In the SVD details, U shows nearby rows; Σ lists these strengths and their eigenvalue connection; Vᵀ shows every channel weight. All 800 U rows are available in the JSON export.')

page('Rank: how many patterns do we keep?','SVD / move the reconstruction slider')
eq('Rank-r approximation: Ẑᵣ = Uᵣ Σᵣ Vᵀᵣ.<br/>Restore original units: X̂ᵣ = Ẑᵣ × s + μ, separately for each channel.')
fig('ranktraces','Recorded A speed. Fewer components miss more detail. These are approximations of the same aligned measurements, not independent predictions.',265)
p_('The slider keeps the first r singular components, ordered by strength. With five selected features, r can be 1 to 5. If you select two features, it can be 1 to 2. Keeping more components cannot increase this transformed-matrix reconstruction error, apart from negligible rounding.')
box('ONE REBUILT NUMBER','For A sample 81, rank 2 reconstructs speed ≈ 269.39441 km/h. The aligned speed is 268.74765 km/h, so observed - reconstructed ≈ -0.64677 km/h. Keeping all five components recovers the aligned table to floating-point precision.')
p_('For one entry, use Σ over the kept components of U[i,k] × σ[k] × Vᵀ[k,j]. Then multiply by the channel scale and add its mean. This is the sum printed in the inspector.')

page('Three different reconstruction scores','SVD / know what each error measures')
fig('rankerrors','Recorded rank sweep. The first graph falls; the second rises. Both describe reconstruction of the same transformed input.',185)
table(['Readout','Definition','Meaning'],[('Retained variation','Σ kept σ² / Σ all σ²','Fraction of transformed variation retained.'),('Relative matrix error','||Z - Ẑ||F / ||Z||F','Total remaining transformed mismatch divided by total input size.'),('Channel RMSE','sqrt(mean((x - x̂)²))','Average-sized channel mismatch in original units.')],[115,192,CW-307])
p_('The <b>Frobenius norm</b> means: square every table entry, add all those squares, then take the square root. A vector’s 2-norm does the same for a list. A relative error has no unit; speed RMSE has km/h.')
box('RECORDED RANK 2','Retained variation = 88.72822%. Relative matrix error ≈ 0.33573. Speed RMSE ≈ 10.28129 km/h across both laps. Relative error is sqrt(1 - retained fraction), not 1 - retained fraction.')
p_('Full-rank relative error is about 7.74 × 10^-16. Read 10^-16 as a decimal point followed by many zeros. It is computer rounding, not proof that the original sensors are perfect. A channel with a low RMSE may coexist with larger errors in another channel.')
ask('Can “88.73% retained” be called prediction accuracy? No. It describes how much variation this reconstruction retains from its own input.')

page('Curve fitting: a smooth speed summary','Curve fitting / a separate mathematical branch')
p_('Suppose you draw a smooth pencil line through a bumpy speed trace. A <b>curve fit</b> chooses numbers defining that smooth line. This module uses a polynomial: a sum of powers of normalised distance.')
eq('Fitted speed v̂(u) = c₀ + c₁u + c₂u² + ... + cₘuᵐ.<br/>m = chosen degree (1 to 5). There are m + 1 coefficients.')
fig('polys','Practice curves only. Powers change a curve’s shape. These coefficients were chosen for illustration, not fitted to F1 data.',190)
p_('Degree 1 is a straight line. Degree 2 allows a quadratic bend. Degree 3 allows a cubic shape. A coefficient c is a recipe number for one power. The constant c₀ is the fitted speed at u = 0; it need not equal the first observed speed.')
box('WHAT THIS FIT USES','It uses each driver’s aligned speed over the selected distance interval. It does not fit PCA scores, throttle or lap position. Both drivers use the same distance grid and interval, but each gets its own coefficients.')
p_('The goal is a descriptive summary, not the physics of an F1 car. A polynomial has no built-in knowledge of corners, braking limits, tyre grip or future traffic. More degree means more flexibility, not an automatic guarantee of a useful explanation.')

page('Why distance becomes u','Curve fitting / normalise the horizontal ruler')
p_('The track distance can be thousands of metres. Taking its fifth power makes huge numbers. The code first changes the selected interval into a ruler from 0 to 1, which makes polynomial powers easier to handle numerically.')
eq('u = (d - origin) / span.<br/>d = aligned distance; origin = first included distance;<br/>span = last included distance - first included distance.')
table(['Practice d','origin = 1000 m; span = 500 m','u'],[('1000 m','(1000 - 1000) / 500','0'),('1250 m','(1250 - 1000) / 500','0.5'),('1500 m','(1500 - 1000) / 500','1')],[100,290,CW-390])
box('SUBSTITUTE A SMALL PRACTICE POLYNOMIAL','Suppose v̂ = 100 + 40u - 20u². At 1250 m, u = 0.5.<br/>v̂ = 100 + 40×0.5 - 20×0.25 = 115 km/h.<br/>If observed speed is 120 km/h, residual = 120 - 115 = +5 km/h.')
p_('The coefficients here belong to powers of <b>u</b>. Do not insert metres directly into the polynomial. u is unitless, so these speed-polynomial coefficients are expressed in km/h. The transformed coordinates change the coefficient interpretation, not the observed speed values.')
p_('The interval is selected using distances on the 400-point grid. The first included point can be slightly after the number typed in From, and the last can be slightly before To. The backend returns the actual origin and span used.')
ask('What is the difference from standardisation? This step rescales the distance axis for fitting. Standardisation transforms the selected feature columns for covariance, PCA and SVD.')
p_('<b>Recorded Leclerc degree-3 recipe:</b> v̂(u) ≈ 319.74011 - 655.91700u + 1229.62520u² - 651.46106u³ km/h. Here origin = 0 m and span ≈ 5366.37201 m. These coefficients describe this particular selected fit, not a universal F1 speed equation.')

page('Least squares: how the curve is chosen','Curve fitting / what the computer minimises')
p_('The computer tries coefficient values, evaluates the polynomial at every included distance, and looks at its mistakes. It chooses coefficients to minimise the <b>sum of squared residuals</b>. The implementation uses SciPy’s curve_fit routine.')
eq('Residual eᵢ = observed speed yᵢ - fitted speed v̂ᵢ.<br/>SSE = Σᵢ eᵢ².<br/>Choose coefficients c₀...cₘ to make SSE as small as possible.')
table(['Practice observation','Candidate fit 1','Candidate fit 2'],[('Observed speeds: 100, 120','Predictions: 100, 100','Predictions: 105, 115'),('Residuals','0, 20','-5, 5'),('Squared errors','0, 400','25, 25'),('SSE','400','50')],[180,160,CW-340])
p_('Candidate 2 wins this comparison because 50 is smaller than 400. That does not mean it is the best possible fit among every candidate; it shows the rule the optimiser follows. Squaring prevents positive and negative errors from cancelling, and gives big misses extra weight.')
h('How many points are enough?')
p_('A degree-m polynomial has m + 1 coefficients, but this implementation requires at least <b>m + 3 included points</b>. Degree 3 therefore requires 6 or more points. Too narrow a distance interval produces an error asking you to widen it.')
box('TRAINING FIT, NOT A FORECAST','The error is measured on the same aligned samples used to choose the coefficients. This module does not hold out a future lap for a prediction test. A small fitting error by itself cannot promise future accuracy.')
ask('Why not minimise the ordinary signed sum of residuals? Large positive and negative mistakes could cancel and hide a poor fit.')

page('Read the actual observed-versus-fit graph','Curve fitting / the example can fit poorly')
fig('fit','Recorded full-overlap degree-3 fits. The dashed smooth curves miss many sharp speed changes. That visible mismatch is a real result.',270)
table(['Driver','RMSE (km/h)','R²'],[('A / Leclerc L12',f'{a["fit"]["drivers"][0]["rmse"]:.3f}',f'{a["fit"]["drivers"][0]["r_squared"]:.5f}'),('B / Verstappen L16',f'{a["fit"]["drivers"][1]["rmse"]:.3f}',f'{a["fit"]["drivers"][1]["r_squared"]:.5f}')])
p_('The horizontal axis is distance and the vertical axis is speed. The recorded line is the aligned measurement. The dashed line is the polynomial evaluation. Where they separate, the model misses the observed shape.')
box('A GOOD EXPLANATION OF A WEAK FIT','“A single cubic is too smooth to represent repeated straights and braking zones over this full lap. Its error is large, so I would show the residuals and try a shorter interval. I would not claim the maths failed or hide the result.”')
p_('Changing the interval asks a different fitting question. Compare fits using the same driver, interval and observations before claiming one is better. A higher degree can bend more, but can oscillate or be misleading outside the fitted interval.')

page('Residuals, RMSE and R²','Curve fitting / three views of a miss')
fig('residuals','Recorded residuals. Above zero means the fit is below the observation; below zero means the fit is above it.',175)
eq('RMSE = sqrt(Σ eᵢ² / Nfit).<br/>R² = 1 - SSE / SST, where SST = Σ(yᵢ - mean(y))².<br/>Nfit = included points per driver, not the combined 800-row matrix.')
p_('RMSE means <b>Root Mean Squared Error</b>: square, average, square-root. It is in km/h for speed. R² compares the squared fitting error with the error from simply predicting the interval’s mean speed every time. R² has no unit.')
table(['Practice: observed 10, 20, 30','Compute it'],[('Predicted 12, 18, 30','Residuals = -2, 2, 0; SSE = 8.'),('Mean observed = 20','SST = 100 + 0 + 100 = 200.'),('RMSE','sqrt(8 / 3) ≈ 1.63299.'),('R²','1 - 8 / 200 = 0.96.')],[220,CW-220])
p_('R² = 1 means no squared error. R² = 0 means the same SSE as the mean-only reference. A negative value means worse than that reference. If every observed value is identical, SST = 0; the app returns no R² instead of dividing by zero. For ordinary well-solved least squares with a constant term on the same data, R² is normally non-negative.')
ask('What should you look for in residuals? Size and patterns. Repeated big waves show a missed shape even if one summary score looks acceptable.')

page('Every top-level mathematics control','Use the module / settings that recompute')
table(['Control','What it does','What to watch'],[('Channel checkboxes','Choose the 2-5 input features.','Changes X columns and the joint decompositions. Fit still uses speed.'),('Standardize channels','Select centred-and-scaled or centred-only input.','Changes covariance, PCA and SVD. Does not standardise the fitting speed.'),('Polynomial degree','Choose 1, 2, 3, 4 or 5.','Changes coefficient count and curve flexibility.'),('From (m), To (m)','Choose distance interval for fitting.','PCA, eigenvectors and SVD still use both full aligned laps.'),('Calculate','Send the draft settings to the backend.','Changed settings are not the displayed new results until calculation completes.'),('Walkthrough / advanced tabs','Choose a way of viewing outputs.','The four advanced tabs expose the same analysis, not new driver ratings.')],[118,205,CW-323])
h('A reliable first exercise')
p_('Use the two selected laps. Keep all five channels and Standardize channels on. Use degree 3 and a wide interval. Press Calculate. Start at Measurements. Choose Speed and use A sample 81 so you can follow the worked example in this guide.')
box('WHEN RESULTS CANNOT BE COMPUTED','You need enough complete telemetry, overlapping distance, at least two selected channels and non-zero overall variation. Fitting needs a valid interval with degree + 3 points. Read the error and change the relevant input; missing telemetry cannot be repaired by an equation.')
p_('For a new pair of laps, the numbers will change. Learn the method, not just the recorded answers. Brake and gear are state channels, so their PCA approximations need special interpretation even when the numerical reconstruction is valid.')

page('Every walkthrough and inspector control','Use the module / inspect without refitting')
table(['Control or action','What changes'],[('Seven stage buttons / Previous / Next','The displayed stage and its explanation. The computed matrices stay the same.'),('Channel selector','Channel shown in traces and the selected channel entry in the inspector.'),('Driver A/B selector','Which driver’s aligned sample is being inspected.'),('Aligned sample slider','Which of that driver’s 400 aligned rows is selected. Display counting starts at 1.'),('Component selector','Eigenvector or PC used for weights, score terms and checks. The PCA scatter remains PC1/PC2.'),('Click a graph point','Select its observation; for eigenvector bars it selects a channel.'),('Click a covariance cell','Select a pair of channels for products and the covariance receipt.'),('SVD rank slider','Choose how many already computed singular components reconstruct the input.'),('Open U, Σ and Vᵀ entries','Expand local U rows, singular strengths and full Vᵀ directions.'),('Matrix row button','Inspect that row from the preview. A rows precede B rows.')],[172,CW-172])
box('READ A CALCULATION RECEIPT','First identify driver, lap, distance, elapsed time and joint row. Then read input x, the mean/scale substitution, and the current stage’s products or reconstruction. The dotted vertical line on distance plots follows the selected sample.')
p_('In Curve fitting, the inspector uses the nearest point inside the fitted interval. If your selected lap sample is outside that interval, the fitting receipt may refer to a different distance. Read the printed “nearest fitted sample” distance instead of assuming it is identical.')
ask('Do you need Calculate after moving the sample slider? No. You are inspecting another already calculated row, not fitting a new model.')

page('The four advanced tabs, decoded','Use the module / a compact second view')
table(['Tab','Graph','Numerical details'],[('PCA','PC1 versus PC2 scatter, one dot per aligned sample.','Inspect component: loadings, shared means and scales; explained variation.'),('Eigenvalues & vectors','Eigenvalue bars: component number versus variance.','Eigenvalue row; one row per feature and one column per eigenvector; expandable covariance matrix.'),('SVD','Singular-value bars: component number versus strength.','σ, σ²/(n - 1), matrix shapes and full-rank relative error.'),('Curve fitting','Recorded and fitted speed against distance.','Per-driver coefficients, degree, normalised-distance formula, RMSE and R².')],[113,195,CW-308])
h('A notation difference to recognise')
p_('The older advanced SVD tab writes <b>X = UΣVᵀ</b> for the matrix being factorised. In the Walkthrough and in this guide, raw aligned inputs are X and transformed inputs are Z. The actual backend SVD is applied to the <b>centred and optionally standardised matrix Z</b>. The label does not mean the raw physical-unit table was decomposed unchanged.')
h('Where to find the most detailed proof')
p_('Use the Walkthrough for observation products, equation substitutions, PC contribution bars, rank reconstruction, residual graphs and matrix downloads. The advanced tabs provide a shorter overview and tables for the same returned results.')
box('READ MATRIX ORIENTATION','Eigenvectors in the eigen table are columns: pick a component column and read down its feature weights. Vᵀ uses directions as rows: pick a row and read across features. Transpose swaps this orientation.')
ask('Does a taller singular-value bar mean more wins? No. It means a stronger variation component in the selected transformed measurement table.')

page('Download the evidence and reproduce a row','Audit / CSV and JSON records')
p_('The buttons at the bottom of the Walkthrough let you keep the numbers used for the graphs. The exports are the calculation evidence; the visible table is only a small rounded preview.')
table(['Export','Contents','Best use'],[('Aligned inputs CSV','Driver, lap, distance_m, elapsed_s, selected raw channels and matching z_ columns.','Check an aligned row or recompute means and scales.'),('All matrices JSON','Driver/lap metadata plus full input arrays, Z, means, scales, covariance, PCA directions/scores, U, singular values, Vᵀ, rank results, fit and audit fields.','Reproduce dot products, decompositions, errors and provenance.')],[105,270,CW-375])
h('Follow one number in five steps')
p_('<b>1.</b> Export while viewing the desired comparison and settings. Record the chosen features and scaling mode.<br/><b>2.</b> In CSV find A sample 81, or B sample 81 after the first 400 data rows. Check distance and lap.<br/><b>3.</b> Recompute (speed - mean_speed) / scale_speed using JSON means/scales.<br/><b>4.</b> Multiply the row’s Q entries by the chosen PCA component weights. Add the products and compare with its score.<br/><b>5.</b> Use full-precision exports for close checks; rounded PDF values only give approximate equality.')
box('ARRAY INDEXING','Printed sample 81 uses array index 80. For B sample 81, joint raw/Z/U index is 480. Scores are split by driver: scores[1][80] is B’s sample. Channel positions follow the exported features list; never assume a fixed order after changing selections.')
p_('With all five channels selected, CSV has 800 data rows and 14 columns: 4 identity/location/time columns + 5 measurements + 5 transformed values. JSON also exposes input_counts, source, pipeline and numerical checks.')

page('What actually happens in the backend','Audit / connect the equations to the implementation')
p_('The browser sends the comparison identifier, selected features, scaling option, degree and fit interval to <b>POST /api/analysis</b>. FastAPI validates the request and looks up the recorded comparison. These named operations then run on its numerical arrays.')
table(['Code / operation','Mathematical job','Returned evidence'],[('backend.analysis.align','Clean, sort, deduplicate and align both laps to shared distance.','distance, audit.raw, aligned_times'),('StandardScaler','Fit shared means and effective scales; transform X into Z.','means, scales, audit.centered'),('numpy.cov','Compute sample covariance of transformed columns.','covariance; ddof = 1'),('numpy.linalg.eigh','Solve symmetric covariance eigendecomposition; sort descending.','eigenvalues, eigenvectors, Cv/λv checks'),('sklearn PCA','Joint full-SVD PCA of the transformed observations.','components, scores, explained_variance, contributions'),('numpy.linalg.svd','Thin SVD of Z and rank-by-rank reconstruction.','u, singular_values, vt, ranks, errors'),('scipy.optimize.curve_fit','Least-squares polynomial on normalised distance for each speed trace.','coefficients, fitted, observed, RMSE, R²')],[133,210,CW-343])
p_('The Walkthrough is a teaching order. Inside the function, PCA, SVD and covariance/eigen calculations are computed from the shared transformed table as related operations; PCA does not consume the separately returned eigenvectors. Fitting is the separate aligned-speed branch.')
box('WHAT THE FRONTEND DOES','It plots returned numeric arrays and reads their entries for receipts. The numbers are produced by these mathematical routines; the graphs are a view of those numbers. There is no AI driver rating inside this mathematics pipeline.')

page('Mistakes to catch before teaching others','Interpretation / questions worth asking')
table(['Tempting statement','More accurate explanation'],[('“PC1 is driving talent.”','PC1 is a variance-maximising direction in these selected measurements.'),('“Negative is bad.”','A sign indicates a direction or difference. Component signs can flip.'),('“The two clouds overlap, so drivers are identical.”','They overlap on two displayed components for these selected laps.'),('“All 800 observations are independent.”','Adjacent aligned distances are related; alignment does not add new sensors.'),('“Covariance proves throttle causes speed.”','It describes joint linear variation, not causation.'),('“Rank 5 means perfect real-world truth.”','It rebuilds the transformed aligned input to numerical precision.'),('“A reconstructed gear of 5.3 is a real gear.”','A low-rank numerical approximation can be fractional; it is not a valid discrete state.'),('“More degree always means better science.”','Flexibility can reduce fitting error yet produce a less useful smooth summary.'),('“From/To filters PCA too.”','The interval affects curve fitting only.'),('“The guide’s numbers must always appear.”','Different laps, features, scaling or intervals change the results.')],[205,CW-205])
p_('Car setup, tyres, fuel, traffic, weather and data quality all influence these measurements. Comparing two laps cannot isolate pure driver skill. These limitations explain the meaning of a graph; they do not make the calculations useless.')
ask('Before naming a pattern, ask: What are the inputs? What are the axes and units? What operation created it? What does the graph support, and what does it leave unknown?')

page('Your five guided experiments','Practice / do this inside Mathematics')
h('1 / Trace one observation')
p_('Keep the recorded settings if available. Select A, sample 81 and Speed. Write raw speed, mean, scale and z. Divide by hand, then check the inspector. Explain why z has no km/h unit when scaling is on.')
h('2 / Compare two places')
p_('Keep the same model. Move from sample 81 to sample 201. Observe the speed and PCA score contributions. Ask which channel terms changed sign or magnitude. A different row changes contributions; the shared loading recipe stays fixed.')
h('3 / Test the rulers')
p_('Record the explained variance ratios. Turn Standardize channels off and Calculate. Inspect the means/scales, loadings and covariance magnitudes. Expect a different numerical balance, often strongly affected by RPM. Then turn it back on and Calculate.')
h('4 / Rebuild with fewer patterns')
p_('Open SVD reconstruction. Select Speed. Move rank 1 → 2 → full rank. Watch the traces, retained variation and relative error. Write why lower error describes input reconstruction rather than future-lap prediction.')
h('5 / Challenge the smooth curve')
p_('Use degree 3 over a full interval; record RMSE and R². Choose a shorter interval, Calculate, and examine residuals. Then compare degrees on that same shorter interval. Explain why scores from different intervals are not a like-for-like contest.')
box('A MINI LAB NOTE FOR EACH EXPERIMENT','Question → selected laps and settings → output numbers/graph → what changed → mathematical reason → what you cannot conclude. Screenshot the relevant graph and keep its JSON export if you want to present evidence.')
p_('No exact target answer is promised for new laps. Your goal is to explain why the operation changes, not to copy a particular number. If complete telemetry is unavailable, use this guide’s recorded figures for the discussion.')

page('Check yourself before the answers','Practice / understanding, not memorising')
p_('Try these on paper. Say the meaning in words before calculating. Answers are on pages 39-40. The practice numbers below are invented for learning.')
table(['No.','Question'],[('1','Speeds are 80, 100 and 120. What is the mean, and what are the centred values?'),('2','A channel value is 130, mean 100 and standard deviation 15. What is z? What does it mean?'),('3','How many rows and columns does X have for two laps, 400 shared distances each and three selected features?'),('4','At 0 m speed is 100; at 10 m speed is 120. What is interpolated speed at 5 m? If gear is 3 then 4, what gear is used at 5 m?'),('5','Centred pairs are (-1, -2), (0, 0), (1, 2). Find their sample cross-covariance.'),('6','For C = [[1, 2], [2, 4]] and v = (1, 2), compute Cv. What is the eigenvalue?'),('7','q = (1, -2), loading w = (0.6, 0.8). What is the component score?'),('8','Two components explain 60% and 25%. How much variation is retained? Is that prediction accuracy?'),('9','What do U, Σ and Vᵀ each contribute to reconstruction?'),('10','Retained fraction is 0.91. What is the relative rank reconstruction error?'),('11','origin = 1000 m, span = 500 m, d = 1250 m. Find u and v̂ for v̂ = 100 + 40u - 20u².'),('12','Observed = 10, 20, 30; predicted = 12, 18, 30. Find residuals, RMSE and R².'),('13','Which results change if you alter only the fit interval and press Calculate?'),('14','Why can full-rank SVD give tiny error even when the sensors are imperfect?')],[35,CW-35])

page('Worked answers: measurements to PCA','Practice / answer key 1')
h('1 / Mean and centring')
p_('(80 + 100 + 120) / 3 = 100. Subtract 100 from each value: -20, 0, 20. You have moved the shared middle to zero.')
h('2 / Standardised value')
p_('z = (130 - 100) / 15 = 30 / 15 = 2. It is two standard deviations above the channel’s mean. It is not twice the raw speed and not a driver grade.')
h('3 / Matrix shape')
p_('Two drivers × 400 distances = 800 rows. Three chosen features = 3 columns. Shape: 800 × 3. Distance is the row address, not another selected PCA feature.')
h('4 / Alignment')
p_('Speed = 100 + 0.5 × (120 - 100) = 110. Gear = 3 because 5 m lies after the 0 m state and before the 10 m state. Gear is not interpolated to 3.5.')
h('5 / Covariance')
p_('Products are 2, 0 and 2. Sum = 4. Sample covariance = 4 / (3 - 1) = 2. Same-side changes give a positive value. This value alone does not establish cause.')
h('6 / Eigenvector')
p_('Cv = (1×1 + 2×2, 2×1 + 4×2) = (5, 10) = 5v. Eigenvalue λ = 5. For variance interpretation, use the matching length-1 vector (1, 2) / sqrt(5).')
h('7 / PCA score')
p_('t = 1×0.6 + (-2)×0.8 = 0.6 - 1.6 = -1.0. The loading vector is length 1 because sqrt(0.6² + 0.8²) = 1. The negative score is a coordinate, not a judgement.')
box('CHECK YOUR EXPLANATION','Can you identify which numbers belong to one row and which belong to the shared model? x and q describe the observation; mean, scale and component weights are shared across the selected table.')

page('Worked answers: SVD and fitting','Practice / answer key 2')
h('8 / Explained variation')
p_('60% + 25% = 85% retained in those two components, leaving 15% in other directions. This is a share of transformed variance, not forecasting accuracy.')
h('9 / SVD pieces')
p_('U gives row-specific singular amounts; Σ supplies strengths; Vᵀ gives channel recipes. Multiply and add them to reconstruct Z. Restore original feature units with X̂ = Ẑ × s + μ.')
h('10 / Relative reconstruction error')
p_('sqrt(1 - 0.91) = sqrt(0.09) = 0.3. The fraction lost in squared magnitude is 9%, but the relative Frobenius error is 0.3, not 0.09.')
h('11 / Normalised distance and polynomial')
p_('u = (1250 - 1000) / 500 = 0.5. v̂ = 100 + 40×0.5 - 20×0.5² = 100 + 20 - 5 = 115 km/h. Inserting 1250 directly for u would be incorrect.')
h('12 / Fitting metrics')
p_('Residuals = -2, +2, 0. SSE = 4 + 4 + 0 = 8. RMSE = sqrt(8 / 3) ≈ 1.63299 in the observed speed unit. Mean = 20; SST = 100 + 0 + 100 = 200. R² = 1 - 8 / 200 = 0.96.')
h('13 / Fit interval')
p_('The included speed points, origin/span, fitted coefficients, curves, residuals, RMSE and R² can change. The covariance, PCA and SVD still use the full aligned selected laps with the same selected features and scaling.')
h('14 / Tiny full-rank error')
p_('All components multiply back to the input to numerical precision. If the input already contains interpolation or sensor errors, those are rebuilt too. Reconstruction does not verify the world outside that table.')

page('A five-minute explanation you can give','Teach-back / tell the complete story')
box('OPENING / 30 SECONDS','“We take two selected laps. At each of 400 shared places we describe the car using chosen channels like speed and throttle. We stack the observations into one table so both drivers use the same mathematical ruler.”')
box('FAIR RULERS / 45 SECONDS','“Each column has a mean and a spread. We subtract the mean and, when standardisation is on, divide by its spread. So a huge RPM number cannot dominate just because of its units. This transformed table is Z.”')
box('PATTERNS AND PICTURE / 90 SECONDS','“Covariance measures how pairs of channels vary together. Eigenvectors describe special pattern directions; eigenvalues say how much spread lies along them. PCA uses those kinds of directions as new axes. Each dot’s score is a sum of channel values times weights. PC1 and PC2 make the picture, but they do not show every detail.”')
box('REBUILD / 60 SECONDS','“SVD takes the transformed table apart into row amounts U, strengths Σ and channel recipes Vᵀ. The rank slider keeps fewer recipes and rebuilds an approximation. More kept variation usually means less reconstruction error. Full rank almost perfectly rebuilds the input, not future performance.”')
box('SEPARATE SMOOTH SUMMARY / 60 SECONDS','“Curve fitting uses aligned speed directly over a chosen interval. It chooses polynomial coefficients to minimise squared errors. Residuals show each miss; RMSE gives a speed-sized error; R² compares against a mean-only guess. A smooth full-lap cubic can fit badly, and that is a result we show honestly.”')
p_('<b>Closing question:</b> “Which graph should I inspect if I want to know why one PCA dot is there?” Answer: the contribution bars and calculation inspector. Demonstrate one selected point, not just the colourful cloud.')

page('Your pocket dictionary / A to P','Reference / names in plain language')
table(['Word','Plain definition and role'],[('Aligned sample','A value at one of the common distance-grid locations; may be interpolated.'),('Audit / provenance','The saved trail of inputs, routines, intermediate arrays and checks.'),('Basis','A set of directions used to describe coordinates in a space.'),('Centring','Subtracting a shared column mean; makes its average near zero.'),('Coefficient','A recipe number, such as c₂ multiplying u² in the fit.'),('Component','A combined pattern direction; not a driver or a separate channel.'),('Contribution','One channel’s q × weight term in a component score.'),('Covariance','Average sample co-variation found from centred products.'),('ddof','Degrees of freedom adjustment: divide by n - ddof.'),('Decomposition','Taking a matrix into factors that multiply back together.'),('Eigenvalue / eigenvector','Stretch/variance and its corresponding special direction.'),('Feature','A chosen mathematical input column, such as speed.'),('Fitted / reconstructed','Computed approximation from a curve or a matrix reconstruction.'),('Frobenius norm','Square root of the sum of squared entries of a whole matrix.'),('Identity matrix I','Square table with diagonal 1s and other entries 0; leaves vectors unchanged.'),('Interpolation','Estimating between recorded neighbours using a stated rule.'),('Loading','A channel’s weight in a principal component.'),('Matrix / vector','A rectangular number table / a number list.'),('Normalisation','Changing a ruler; here fit distance is mapped to u from 0 to 1.'),('Observation','One row: selected channel values at one aligned location for one driver.'),('Orthogonal','Perpendicular; unit orthogonal vectors also have length 1.'),('PCA / projection','Principal Component Analysis / coordinates found by dot products.')],[130,CW-130])

page('Your pocket dictionary / R to Z','Reference / names, symbols and checks')
table(['Word','Plain definition and role'],[('Rank r','Number of singular components kept; mathematical rank counts independent directions.'),('Residual','Observed minus approximated value; sign says which is larger.'),('RMSE','Root Mean Squared Error; typical-sized squared-error measure in channel units.'),('R²','1 - SSE/SST; comparison with a mean-only fit on the same interval.'),('Score t','An observation’s coordinate along a principal component.'),('Singular value σ','A non-negative component strength in SVD.'),('SSE / SST','Sum of squared errors / total squared deviations from the observed mean.'),('Standard deviation s','Square root of average squared deviation from a mean.'),('Standardisation','Subtract the mean and divide by effective standard deviation.'),('SVD','Singular Value Decomposition: Z = UΣVᵀ.'),('Thin SVD','The compact factor shapes used here: U has p rather than n columns.'),('Transpose T','Swap rows and columns, as in Vᵀ.'),('Variance','Squared spread; for a unit eigenvector, the corresponding eigenvalue.'),('X, Z, Q','Raw aligned features; transformed features; Z with its residual mean removed.'),('μ, λ, Σ','Column mean; eigenvalue; in SVD, diagonal singular-strength matrix.'),('u, d, c, m','Normalised fit distance; metres; coefficients; polynomial degree.'),('n, p, Nfit','Combined row count; selected feature count; fitting points per driver.')],[130,CW-130])
h('Three quick formula checks')
p_('<b>Standardisation:</b> z = (x - μ) / s; reverse x = z × s + μ.<br/><b>Covariance:</b> C = QᵀQ / (n - 1); eigen check Cv = λv.<br/><b>Projection:</b> t = sum of q × loading; reconstruction uses sum of U × σ × Vᵀ.')
p_('You have mastered the story when you can name each input, read each axis, trace one row to a score, explain one reconstruction, and show why a polynomial misses a braking zone. Keep asking “which number, which ruler, which operation?”')

page('Where the examples and explanations come from','Reference / reproducibility and scope')
p_('This guide was checked against the local project implementation dated 22 October 2026. It explains the Mathematics module as implemented, including its current limitations. It does not claim to be an official Formula 1 guide or an official statistical assessment of driver skill.')
h('Project sources used')
table(['Source in the project','What was checked'],[('backend/analysis.py','Alignment, scaler, PCA, covariance/eigensystem, SVD/rank reconstruction, fitting and audit arrays.'),('backend/main.py','Analysis request validation and endpoint behaviour.'),('frontend/src/MathJourney.tsx','Seven stages, graph axes, inspector, controls, downloads and displayed substitutions.'),('frontend/src/Mathematics.tsx','Shared controls and the four advanced tabs.'),('docs/math-guide-example.json','Saved numerical output used to draw the recorded figures and verify worked values.')],[202,CW-202])
h('Recorded data, not practice data')
p_('The saved example compares 2024 Bahrain Qualifying, Leclerc L12 and Verstappen L16. The calculation record identifies FastF1 driver identities/calendar and OpenF1 historical timing/telemetry as its data sources. It contains 687 and 700 source samples, aligned to 400 locations per driver, with all five features standardised. The fitting example uses degree 3 over the full shared range, about 0-5366.372 m.')
p_('All plots labelled Recorded are redrawn from that saved backend output. Small practice examples, including the two-channel eigenvector and compact SVD exercises, are invented and explicitly labelled. Charts use print-friendly versions of the project’s coral/cyan colours; the underlying values are unchanged.')
box('CHECKING A FUTURE VERSION','Export your current JSON, compare feature order and settings, and read its pipeline/source fields. New laps or code changes may give different counts or values. The companion generator rebuilds this guide from its saved example. Using a different record requires updating the written example and its labels as well as the figures.')
p_('<b>End of the Mathematics-only guide.</b> Use the quiz and five-minute explanation again after a break. Understanding means you can connect the words, equations, graphs and the actual number trail.')
check(); c.save()
assert page_no==44, (page_no,pages)
assert not overflows, overflows
(ROOT/'docs/math-guide-pages.json').write_text(json.dumps({'title':'F1 Driver DNA Mathematics Guide','pages':[{'page':i+1,'title':t} for i,t in enumerate(pages)]},indent=2))
print(f'Created {page_no} pages: {OUT}')
