"""本地仪表盘页面（单文件 HTML/CSS/JS，无外部依赖）。"""
from __future__ import annotations

PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hot100 训练台</title>
<style>
:root{
  --bg:#0a1120; --panel:#101b2e; --panel2:#0d1728; --line:#1e2e4a;
  --text:#e8effa; --muted:#8ea3c0; --dim:#61748f;
  --teal:#2dd4bf; --teal-d:#0f766e; --amber:#f5b64a; --red:#f87171;
  --green:#4ade80; --blue:#60a5fa; --shadow:0 18px 50px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:
    radial-gradient(900px 500px at 12% -10%, rgba(45,212,191,.10), transparent 60%),
    radial-gradient(800px 460px at 100% 0%, rgba(96,165,250,.08), transparent 55%),
    var(--bg);
  color:var(--text);
  font-family:"Microsoft YaHei UI","Segoe UI",system-ui,-apple-system,sans-serif;
  min-height:100vh; font-size:14px;
}
button,input,select,textarea{font-family:inherit}
button{cursor:pointer}
.hidden{display:none!important}
.wrap{max-width:1180px;margin:0 auto;padding:22px 22px 60px}
.top{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;margin-bottom:18px}
.brand{font-size:23px;font-weight:800;letter-spacing:2px}
.brand span{color:var(--teal);font-weight:600;letter-spacing:6px;margin-left:6px;font-size:15px}
.brand small{display:block;color:var(--dim);font-size:11px;letter-spacing:1px;font-weight:400;margin-top:5px}
.topright{display:flex;gap:10px;align-items:center;flex-wrap:wrap;justify-content:flex-end}
.chip{background:rgba(45,212,191,.08);border:1px solid rgba(45,212,191,.28);color:#a7f3d0;
  border-radius:99px;padding:5px 12px;font-size:12px;white-space:nowrap}
.chip.dim{background:#131f33;border-color:var(--line);color:var(--muted)}
.iconbtn{background:#16233a;border:1px solid var(--line);color:var(--muted);border-radius:9px;
  padding:7px 12px;font-size:12px}
.iconbtn:hover{color:var(--text);border-color:#2d435f}
.warn{background:rgba(245,182,74,.08);border:1px solid rgba(245,182,74,.3);color:#fcd9a0;
  border-radius:12px;padding:11px 14px;font-size:12.5px;line-height:1.7;margin-bottom:16px}
.main{display:grid;grid-template-columns:1.55fr 1fr;gap:16px;align-items:start}
@media (max-width:940px){.main{grid-template-columns:1fr}.right{order:-1}}
.panel{background:linear-gradient(180deg,rgba(19,31,50,.92),rgba(14,24,40,.92));
  border:1px solid var(--line);border-radius:15px;box-shadow:var(--shadow)}
.pad{padding:16px 18px}
.statgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px}
.stat{background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.stat b{display:block;font-size:21px;letter-spacing:.5px}
.stat span{color:var(--dim);font-size:11.5px}
.progressline{margin-top:2px}
.pbar{height:7px;background:#0a1526;border:1px solid #1a2a45;border-radius:99px;overflow:hidden}
.pbar i{display:block;height:100%;background:linear-gradient(90deg,#14b8a6,#2dd4bf);border-radius:99px;
  transition:width .5s ease}
.pmeta{display:flex;justify-content:space-between;color:var(--dim);font-size:11px;margin-top:6px}
.sect-head{display:flex;align-items:center;justify-content:space-between;margin:2px 0 6px}
.sect-head h2{font-size:14px;margin:0;letter-spacing:1px;font-weight:700}
.sect-head span{color:var(--dim);font-size:11.5px}
.items{display:flex;flex-direction:column;gap:7px;margin-top:10px}
.item{display:grid;grid-template-columns:52px 14px 1fr auto;gap:10px;align-items:center;
  padding:11px 12px;border-radius:11px;border:1px solid transparent;background:#0d1728;
  cursor:pointer;transition:.15s}
.item:hover{background:#122036;border-color:#223752}
.item.sel{border-color:rgba(45,212,191,.55);background:linear-gradient(90deg,rgba(45,212,191,.10),rgba(13,23,40,.9))}
.item.done{opacity:.62}
.item.doing{box-shadow:inset 3px 0 0 var(--teal)}
.item.expired{opacity:.42}
.time{font-variant-numeric:tabular-nums;color:#c3d3e8;font-size:12px;line-height:1.4}
.time span{display:block;color:var(--dim);font-size:10.5px}
.dot{width:8px;height:8px;border-radius:99px;background:#314865;justify-self:center}
.dot.done{background:var(--green)} .dot.doing{background:var(--teal);box-shadow:0 0 0 4px rgba(45,212,191,.13)}
.dot.unfinished{background:var(--red)}
.ititle{font-size:13.5px;font-weight:600;display:flex;align-items:baseline;gap:7px}
.ititle em{font-style:normal;color:var(--dim);font-size:11px;font-weight:400}
.isub{color:var(--dim);font-size:11px;margin-top:3px;line-height:1.5}
.pill{border-radius:99px;padding:3px 9px;font-size:10.5px;white-space:nowrap;border:1px solid transparent}
.pill.muted{color:#8296b1;background:#142237;border-color:#203350}
.pill.live{color:#99f6e4;background:rgba(45,212,191,.1);border-color:rgba(45,212,191,.35)}
.pill.ok{color:#bbf7d0;background:rgba(74,222,128,.1);border-color:rgba(74,222,128,.3)}
.pill.warn{color:#fde68a;background:rgba(245,182,74,.1);border-color:rgba(245,182,74,.32)}
.pill.bad{color:#fecaca;background:rgba(248,113,113,.1);border-color:rgba(248,113,113,.3)}
.pill.info{color:#bfdbfe;background:rgba(96,165,250,.1);border-color:rgba(96,165,250,.3)}
.timer{padding:18px}
.kicker{color:var(--teal);font-size:10.5px;letter-spacing:2px}
.timer h2{font-size:19px;margin:6px 0 3px;line-height:1.35}
.timer .meta{color:var(--dim);font-size:11.5px}
.thead{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}
.clock{display:flex;align-items:baseline;gap:8px;margin:18px 0 8px;font-variant-numeric:tabular-nums}
.clock b{font-size:40px;letter-spacing:1px;font-weight:700;line-height:1}
.clock span{color:var(--dim);font-size:12px}
.clock.over b{color:var(--red)}
.tbar{height:8px;background:#0a1526;border:1px solid #1a2a45;border-radius:99px;overflow:hidden}
.tbar i{display:block;height:100%;width:0;background:linear-gradient(90deg,#0d9488,#2dd4bf);transition:width .6s}
.tbar.over i{background:linear-gradient(90deg,#b91c1c,#f87171)}
.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:15px}
.btn{border:1px solid var(--line);background:#16233a;color:#d7e3f4;border-radius:9px;
  padding:8px 13px;font-size:12px;transition:.15s}
.btn:hover{border-color:#33506f;background:#1a2b45}
.btn.primary{background:var(--teal-d);border-color:#14b8a6;color:#f0fdfa;font-weight:700}
.btn.primary:hover{background:#0d9488}
.btn.danger{background:rgba(248,113,113,.12);border-color:rgba(248,113,113,.35);color:#fecaca}
.btn.ghost{background:transparent}
.btn:disabled{opacity:.4;cursor:not-allowed}
.tip{color:var(--dim);font-size:11.5px;line-height:1.7}
.donebox{margin-top:14px;background:rgba(74,222,128,.06);border:1px solid rgba(74,222,128,.22);
  border-radius:10px;padding:10px 12px;font-size:12px;color:#c8f7d8;line-height:1.7}
.donebox b{color:#eafff1}
.side{display:flex;flex-direction:column;gap:16px}
.recent{padding:15px 17px}
.rrow{display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px dashed #1b2a43;font-size:12px}
.rrow:last-child{border-bottom:0}
.rrow .t{color:#c9d8ec}
.rrow .m{color:var(--dim);font-size:11px;white-space:nowrap}
.empty{color:var(--dim);font-size:12.5px;padding:14px 2px;line-height:1.8}
footer{margin-top:22px;color:#4f637e;font-size:11px;line-height:1.8;text-align:center}
/* modal */
.overlay{position:fixed;inset:0;background:rgba(4,8,16,.72);backdrop-filter:blur(3px);
  display:flex;align-items:flex-start;justify-content:center;padding:5vh 18px;z-index:50;overflow:auto}
.modal{width:min(760px,100%);background:#0f1a2d;border:1px solid #263a58;border-radius:16px;
  box-shadow:0 30px 80px rgba(0,0,0,.55);animation:pop .18s ease}
.modal.wide{width:min(940px,100%)}
@keyframes pop{from{transform:translateY(8px);opacity:.5}to{transform:none;opacity:1}}
.mhead{display:flex;align-items:center;justify-content:space-between;padding:15px 20px;border-bottom:1px solid var(--line)}
.mhead h3{margin:0;font-size:15px;letter-spacing:.5px}
.mclose{background:transparent;border:0;color:var(--dim);font-size:20px;line-height:1;padding:2px 6px}
.mclose:hover{color:var(--text)}
.mbody{padding:18px 20px 20px}
.md{line-height:1.85;font-size:13.5px;color:#d3e0f0}
.md h1{font-size:20px;margin:0 0 12px}
.md h2{font-size:14px;color:var(--teal);margin:22px 0 8px;letter-spacing:.5px}
.md p{margin:8px 0}
.md ul{margin:8px 0;padding-left:20px}
.md li{margin:4px 0}
.md code{background:#0a1423;border:1px solid #1d2e48;border-radius:5px;padding:1px 5px;
  font-family:Consolas,"Cascadia Mono",monospace;font-size:12px;color:#a5f3ec}
.md pre{background:#081120;border:1px solid #1b2b45;border-radius:10px;padding:12px 14px;
  overflow:auto;font-size:12.5px;line-height:1.6}
.md pre code{background:none;border:0;padding:0;color:#d6e6f8}
.md a{color:var(--teal)}
.code{background:#081120;border:1px solid #1b2b45;border-radius:10px;padding:13px 15px;
  overflow:auto;font-family:Consolas,"Cascadia Mono",monospace;font-size:12.3px;line-height:1.62;
  color:#d6e6f8;max-height:52vh;white-space:pre}
.gate{background:rgba(245,182,74,.07);border:1px solid rgba(245,182,74,.28);color:#fde2b3;
  border-radius:11px;padding:12px 14px;font-size:12.5px;line-height:1.8;margin-bottom:14px}
.gate b{color:#ffedc7}
.opt{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}
.opt label{flex:1 1 150px;border:1px solid var(--line);border-radius:10px;padding:10px 12px;
  cursor:pointer;background:#0c1626;font-size:12.5px}
.opt label:hover{border-color:#2d4a6b}
.opt input{margin-right:6px;accent-color:#14b8a6}
.opt small{display:block;color:var(--dim);font-size:10.5px;margin-top:3px;line-height:1.5}
.field{margin:11px 0}
.field label{display:block;color:var(--muted);font-size:11.5px;margin-bottom:5px}
.field input,.field textarea,.field select{width:100%;background:#0a1526;border:1px solid #223553;
  color:var(--text);border-radius:9px;padding:9px 11px;font-size:12.5px;outline:none}
.field input:focus,.field textarea:focus{border-color:#2f6f68}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.check{display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--muted);margin:9px 0}
.check input{accent-color:#14b8a6}
.mfoot{display:flex;justify-content:flex-end;gap:9px;margin-top:16px}
.res{border:1px solid var(--line);border-radius:9px;padding:9px 12px;margin:7px 0;font-size:12px}
.reshead{display:flex;justify-content:space-between;gap:10px;align-items:center}
.res.ok{border-color:rgba(74,222,128,.3);background:rgba(74,222,128,.05)}
.res.bad{border-color:rgba(248,113,113,.3);background:rgba(248,113,113,.05)}
.res pre{white-space:pre-wrap;color:var(--dim);font-size:11px;margin:6px 0 0;max-height:160px;overflow:auto}
.editor{width:100%;height:46vh;min-height:280px;background:#081120;color:#d9e8fb;
  border:1px solid #223553;border-radius:10px;padding:13px 15px;outline:none;resize:vertical;
  font-family:Consolas,"Cascadia Mono",monospace;font-size:13px;line-height:1.65;
  tab-size:4;white-space:pre;overflow:auto}
.editor:focus{border-color:#2f6f68;box-shadow:0 0 0 3px rgba(20,184,166,.08)}
.codebar{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:10px 0 4px;flex-wrap:wrap}
.codestate{color:var(--dim);font-size:11.5px}
.codehint{color:var(--muted);font-size:11.5px;line-height:1.7;margin:2px 0 8px}
.hintbox{background:#0b1729;border:1px solid #223a5a;border-left:3px solid var(--amber);
  border-radius:10px;padding:13px 15px;font-size:13.5px;line-height:1.85;color:#f4e3bd}
.tabs{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}
.tab{border:1px solid var(--line);background:#0c1626;color:var(--muted);border-radius:8px;padding:6px 12px;font-size:12px}
.tab.on{border-color:rgba(45,212,191,.5);color:#99f6e4;background:rgba(45,212,191,.08)}
.toast{position:fixed;left:50%;bottom:26px;transform:translateX(-50%) translateY(10px);
  background:#13223a;border:1px solid #2b4668;color:#e6f0ff;padding:10px 16px;border-radius:10px;
  font-size:12.5px;opacity:0;pointer-events:none;transition:.2s;z-index:99;max-width:80vw}
.toast.show{opacity:1;transform:translateX(-50%)}
.spin{display:inline-block;width:12px;height:12px;border:2px solid rgba(255,255,255,.25);
  border-top-color:#fff;border-radius:50%;animation:sp .7s linear infinite;vertical-align:-2px;margin-right:6px}
@keyframes sp{to{transform:rotate(360deg)}}
/* scrollbars */
::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-track{background:#0a1424}
::-webkit-scrollbar-thumb{background:#1e3350;border-radius:99px;border:2px solid #0a1424}
::-webkit-scrollbar-thumb:hover{background:#2c4a70}
::-webkit-scrollbar-corner{background:#0a1424}
/* coding workspace */
.ws{position:fixed;inset:0;z-index:40;display:flex;flex-direction:column;
  background:
    radial-gradient(1000px 520px at 8% -12%, rgba(45,212,191,.09), transparent 60%),
    radial-gradient(820px 460px at 102% -4%, rgba(96,165,250,.08), transparent 55%),
    var(--bg)}
.wshead{display:flex;align-items:center;gap:14px;padding:10px 16px;flex-wrap:wrap;
  border-bottom:1px solid var(--line);background:rgba(13,23,40,.92)}
.wsleft{display:flex;align-items:center;gap:11px;min-width:0}
.wsclose{background:#16233a;border:1px solid var(--line);color:var(--muted);border-radius:9px;
  width:32px;height:32px;font-size:15px;line-height:1;flex:none}
.wsclose:hover{color:var(--text);border-color:#2d435f}
.wstitle{display:flex;align-items:center;gap:9px;min-width:0}
.wstitle b{font-size:14.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:34vw}
.wsmini{padding:4px 9px;font-size:11px}
.wsmodes{display:flex;border:1px solid #24405e;border-radius:10px;overflow:hidden;flex:none}
.wsmodes button{background:#0c1626;border:0;color:var(--muted);padding:8px 16px;font-size:12.5px;transition:.15s}
.wsmodes button + button{border-left:1px solid #24405e}
.wsmodes button.on{background:linear-gradient(180deg,rgba(45,212,191,.24),rgba(45,212,191,.09));
  color:#99f6e4;font-weight:700;text-shadow:0 0 12px rgba(45,212,191,.35)}
.wsright{display:flex;align-items:center;gap:8px;margin-left:auto;flex-wrap:wrap}
.wsright kbd{background:#0a1526;border:1px solid #223553;border-radius:4px;padding:0 4px;
  font-size:10px;margin-left:5px;font-family:inherit;color:var(--dim)}
.pcchip{display:inline-flex;align-items:center;gap:7px;font-size:11.5px;color:var(--muted);
  border:1px solid var(--line);border-radius:99px;padding:5px 12px;background:#0c1626;cursor:default;white-space:nowrap}
.pcchip i{width:7px;height:7px;border-radius:99px;background:#3f5878;flex:none}
.pcchip.ok{color:#bbf7d0;border-color:rgba(74,222,128,.3)}
.pcchip.ok i{background:var(--green);box-shadow:0 0 8px rgba(74,222,128,.65)}
.pcchip.err{color:#fecaca;border-color:rgba(248,113,113,.45);cursor:pointer}
.pcchip.err i{background:var(--red);box-shadow:0 0 8px rgba(248,113,113,.6)}
.pcchip.busy i{background:var(--amber);animation:pcp 1s ease infinite}
@keyframes pcp{50%{opacity:.35}}
.wsbody{flex:1;display:grid;grid-template-columns:1.25fr 1fr;gap:14px;padding:14px 16px;min-height:0}
.wspanel{background:linear-gradient(180deg,rgba(19,31,50,.94),rgba(13,22,38,.94));
  border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);
  display:flex;flex-direction:column;min-height:0;overflow:hidden}
.edtop{display:flex;justify-content:space-between;gap:10px;padding:8px 13px;
  border-bottom:1px solid var(--line);font-size:11px;color:var(--dim);flex-wrap:wrap}
.edtop span:first-child{font-family:Consolas,"Cascadia Mono",monospace;color:#7f95b3}
.edwrap{flex:1;display:flex;min-height:0;background:#081120}
.gutter{width:52px;flex:none;background:#0a1424;border-right:1px solid #16233c;user-select:none}
.gutter > div{height:100%;overflow:hidden;padding:12px 0;color:#41597c;
  font-family:Consolas,"Cascadia Mono",monospace;font-size:12px;line-height:21px;text-align:right}
.gutter div div{height:21px;padding-right:10px}
.gutter div div.err{color:#fca5a5;background:rgba(248,113,113,.14);font-weight:700}
.edmain{position:relative;flex:1;min-width:0}
.edhl,.edmain textarea{position:absolute;inset:0;margin:0;border:0;padding:12px 14px;
  font-family:Consolas,"Cascadia Mono",monospace;font-size:13px;line-height:21px;
  tab-size:4;white-space:pre;overflow:auto}
.edhl{pointer-events:none;color:#d6e6f8;overflow:hidden;z-index:1}
.edmain textarea{background:transparent;color:transparent;caret-color:#5eead4;resize:none;
  outline:none;z-index:2;overflow:auto}
.edmain textarea::selection{background:rgba(45,212,191,.28)}
.tk-c{color:#54708f;font-style:italic}
.tk-s{color:#86efac}
.tk-k{color:#c4b5fd}
.tk-b{color:#fca5a5}
.tk-u{color:#7dd3fc}
.tk-d{color:#f5b64a}
.tk-n{color:#f5b64a}
.tk-f{color:#5eead4}
.edstatus{display:flex;justify-content:space-between;gap:10px;padding:6px 13px;
  border-top:1px solid var(--line);font-size:11px;color:var(--dim);font-variant-numeric:tabular-nums}
.respanel{padding:14px 15px}
.reshead2{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px}
.reshead2 h3{margin:0;font-size:13.5px;letter-spacing:1px}
.metrics{display:flex;gap:15px;align-items:center;padding:11px 13px;margin-bottom:11px;
  background:#0c1626;border:1px solid var(--line);border-radius:12px}
.ringbox{flex:none}
.mgrid{flex:1;display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.mcell{background:#0a1424;border:1px solid #1a2a45;border-radius:9px;padding:7px 9px;text-align:center}
.mcell b{display:block;font-size:16px;font-variant-numeric:tabular-nums}
.mcell span{color:var(--dim);font-size:10px}
.mcell.ok b{color:var(--green)} .mcell.warn b{color:var(--amber)} .mcell.bad b{color:var(--red)}
.mcell.wide{grid-column:1/-1;display:flex;align-items:baseline;justify-content:center;gap:8px;flex-wrap:wrap;row-gap:2px}
.mcell.wide b{font-size:13px;color:#c3d3e8}
.caselist{flex:1;overflow:auto;min-height:0;padding-right:3px}
.caseintro{color:var(--muted);font-size:12px;line-height:1.7;margin:2px 0 10px;
  background:rgba(96,165,250,.06);border:1px solid rgba(96,165,250,.22);border-radius:10px;padding:9px 12px}
.caseintro b{color:#bfdbfe}
.case{border:1px solid var(--line);border-radius:10px;margin:8px 0;background:#0c1626;overflow:hidden}
.case.good{border-color:rgba(74,222,128,.26)}
.case.bad{border-color:rgba(248,113,113,.34)}
.casehead{display:flex;justify-content:space-between;align-items:center;gap:10px;
  padding:9px 12px;cursor:pointer;font-size:12px;user-select:none}
.casehead:hover{background:#101d33}
.casehead .pill{margin-left:7px}
.casems{color:var(--dim);font-size:11px;font-variant-numeric:tabular-nums}
.casebody{display:none;padding:2px 12px 12px}
.case.open .casebody{display:block}
.io{margin:7px 0}
.io label{display:block;font-size:10px;color:var(--dim);letter-spacing:1.5px;margin-bottom:4px}
.io pre{margin:0;background:#081120;border:1px solid #16233c;border-radius:8px;padding:8px 10px;
  font-family:Consolas,"Cascadia Mono",monospace;font-size:11.5px;line-height:1.55;color:#c9d8ec;
  max-height:170px;overflow:auto;white-space:pre-wrap;word-break:break-all}
.casedetail{margin:8px 0 0;background:rgba(248,113,113,.07);border:1px solid rgba(248,113,113,.28);
  border-radius:8px;padding:8px 10px;font-size:11.5px;line-height:1.65;color:#fecaca;
  white-space:pre-wrap;word-break:break-all;max-height:180px;overflow:auto}
.casenote{margin:8px 0 0;color:var(--amber);font-size:11px;line-height:1.6}
@media (max-width:920px){
  .wsbody{grid-template-columns:1fr;grid-template-rows:minmax(340px,52vh) minmax(320px,1fr);overflow:auto}
  .wshead{padding:8px 10px;gap:8px}
  .wstitle b{max-width:40vw;font-size:13.5px}
  .wsmini{padding:3px 8px;font-size:10.5px}
  .wsmodes button{padding:7px 12px;font-size:12px}
  .wsright{margin-left:0;gap:6px}
  .wsright kbd{display:none}
  .wsright .btn{padding:7px 10px;font-size:11.5px}
  .pcchip{padding:4px 10px;font-size:10.5px}
  .mgrid{grid-template-columns:repeat(2,1fr)}
  .metrics{gap:10px;padding:9px 10px}
}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div class="brand">HOT 100<span>训练台</span>
      <small>ACM / 核心代码 · Python · 25 分钟一题</small>
    </div>
    <div class="topright">
      <span class="chip" id="dateChip">--</span>
      <span class="chip dim" id="deadlineChip">截止 --</span>
      <button class="iconbtn" id="btnSettings">设置</button>
      <button class="iconbtn" id="btnReplan">重排今日</button>
    </div>
  </div>

  <div class="warn hidden" id="warnBox"></div>

  <div class="main">
    <section class="left">
      <div class="statgrid">
        <div class="stat"><b id="statDone">0</b><span>已完成 / 总题数</span></div>
        <div class="stat"><b id="statToday">0</b><span>今日完成</span></div>
        <div class="stat"><b id="statMinutes">0</b><span>今日分钟</span></div>
        <div class="stat"><b id="statLeft">0</b><span>剩余题数</span></div>
      </div>
      <div class="panel pad progressline">
        <div class="pbar"><i id="globalBar" style="width:0%"></i></div>
        <div class="pmeta"><span id="progressText">--</span><span id="paceText">--</span></div>
      </div>

      <div class="panel pad" style="margin-top:16px">
        <div class="sect-head">
          <h2>今日安排</h2>
          <span id="planMeta">--</span>
        </div>
        <div class="items" id="items"><div class="empty">正在加载…</div></div>
      </div>

      <div class="panel recent" style="margin-top:16px">
        <div class="sect-head"><h2>最近记录</h2><span>完成状态会决定复习间隔</span></div>
        <div id="recent"><div class="empty">还没有记录。</div></div>
      </div>
    </section>

    <aside class="right side">
      <div class="panel timer" id="timerCard">
        <div class="empty">正在加载…</div>
      </div>
      <div class="panel pad">
        <div class="sect-head"><h2>今日节奏</h2><span id="paceMeta">--</span></div>
        <div class="tip" id="rhythm">新题 25 分钟、复习 15 分钟。超时不算失败，先标记状态，明天会优先重排。</div>
        <div class="actions">
          <button class="btn primary" id="btnCodeQuick">写代码</button>
          <button class="btn ghost" id="btnStatementQuick">看题面</button>
          <button class="btn ghost" id="btnHintQuick">要提示</button>
          <button class="btn ghost" id="btnRefQuick">参考答案</button>
        </div>
      </div>
      <div class="panel pad">
        <div class="sect-head"><h2>状态说明</h2></div>
        <div class="tip">
          <b style="color:#bbf7d0">独立完成</b>：不看提示、不看题解。<br>
          <b style="color:#fde68a">借提示完成</b>：用过提示，1 天和 5 天后复习。<br>
          <b style="color:#bfdbfe">看题解后复现</b>：看过参考，1 天和 4 天后复习。<br>
          <b style="color:#fecaca">未完成</b>：明天优先重新安排。
        </div>
      </div>
    </aside>
  </div>
  <footer>本地运行 · 数据保存在 data/state.db · 关闭页面不会丢失进度</footer>
</div>

<div class="overlay hidden" id="overlay">
  <div class="modal">
    <div class="mhead"><h3 id="modalTitle"></h3><button class="mclose" id="modalClose">×</button></div>
    <div class="mbody" id="modalBody"></div>
  </div>
</div>

<div class="ws hidden" id="ws">
  <div class="wshead">
    <div class="wsleft">
      <button class="wsclose" id="wsBack" title="返回仪表盘（Esc）">←</button>
      <div class="wstitle">
        <b id="wsTitle">#--</b>
        <span class="pill muted" id="wsDiff">--</span>
        <button class="btn ghost wsmini" id="wsStatement">题面</button>
      </div>
    </div>
    <div class="wsmodes" id="wsModes">
      <button data-mode="acm" class="on">ACM 模式</button>
      <button data-mode="core">核心代码模式</button>
    </div>
    <div class="wsright">
      <span class="pcchip" id="wsPc" title="后台自动预编译，无需手动操作"><i></i>预编译待命</span>
      <button class="btn ghost" id="wsReset">重置模板</button>
      <button class="btn" id="wsSave">保存<kbd>Ctrl+S</kbd></button>
      <button class="btn primary" id="wsRun">运行全部用例<kbd>Ctrl+↵</kbd></button>
    </div>
  </div>
  <div class="wsbody">
    <div class="wspanel">
      <div class="edtop"><span id="wsFile">--</span><span id="wsModeDoc">--</span></div>
      <div class="edwrap">
        <div class="gutter"><div id="wsGutter"></div></div>
        <div class="edmain">
          <pre class="edhl" id="wsHl" aria-hidden="true"></pre>
          <textarea id="wsArea" spellcheck="false" autocapitalize="off" autocomplete="off" wrap="off"></textarea>
        </div>
      </div>
      <div class="edstatus"><span id="wsPos">行 1，列 1</span><span id="wsSaveState">就绪</span></div>
    </div>
    <div class="wspanel respanel">
      <div class="reshead2"><h3>用例结果</h3><span class="pill muted" id="wsBest">尚未运行</span></div>
      <div class="metrics hidden" id="wsMetrics"></div>
      <div class="caselist" id="wsCases"><div class="empty">正在加载…</div></div>
    </div>
  </div>
</div>
<div class="toast" id="toast"></div>

<script>
const $ = (s) => document.querySelector(s);
const esc = (v) => String(v == null ? "" : v).replace(/[&<>"']/g, (c) => (
  {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]
));
const STATUS = {
  pending:["未开始","muted"], doing:["进行中","live"], done:["已完成","ok"],
  unfinished:["未完成","bad"], expired:["已过期","muted"]
};
const RESULT = {
  done:["独立完成","ok"], hinted:["借提示完成","warn"],
  rewritten:["看题解后复现","info"], unfinished:["未完成","bad"]
};
let state = null, selectedId = null, busy = false, lastRefresh = 0;

function toast(msg){
  const el = $("#toast"); el.textContent = msg; el.classList.add("show");
  clearTimeout(el._t); el._t = setTimeout(() => el.classList.remove("show"), 2600);
}
async function api(path, body){
  const opt = body === undefined ? {} : {
    method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)
  };
  const res = await fetch(path, opt);
  const data = await res.json().catch(() => ({ok:false, error:"响应不是 JSON"}));
  if(!res.ok || data.ok === false) throw new Error(data.error || ("HTTP " + res.status));
  return data;
}
function fmtClock(sec){
  sec = Math.max(0, Math.floor(sec));
  const m = String(Math.floor(sec/60)).padStart(2,"0");
  const s = String(sec%60).padStart(2,"0");
  return m + ":" + s;
}
function minutes(sec){ return Math.max(0, Math.round(sec/60)); }
function parseDT(s){ return s ? new Date(s.replace(" ","T")) : null; }
function activeItem(){
  if(!state) return null;
  return state.items.find(i => i.id === state.current_item_id) || null;
}
function currentItem(){
  if(!state) return null;
  return state.items.find(i => i.id === selectedId) || activeItem() || state.items.find(i => i.status !== "done") || state.items[0] || null;
}
function itemResult(i){
  const s = i.session || {};
  return s.result || (i.status === "done" ? "done" : null);
}

function render(){
  if(!state) return;
  const p = state.progress || {};
  const total = p.total || 0, done = p.done || 0;
  $("#dateChip").textContent = state.day_week;
  $("#deadlineChip").textContent = "截止 " + state.deadline;
  $("#statDone").textContent = done + " / " + total;
  $("#statToday").textContent = p.sessions_today || 0;
  $("#statMinutes").textContent = p.minutes_today || 0;
  $("#statLeft").textContent = p.remaining || 0;
  const pct = total ? Math.round(done * 100 / total) : 0;
  $("#globalBar").style.width = pct + "%";
  $("#progressText").textContent = "总进度 " + pct + "% · 还剩 " + (p.remaining || 0) + " 题";
  $("#paceText").textContent = "距截止 " + state.days_left + " 天 · 今日目标 " + state.target_new + " 道新题";
  $("#planMeta").textContent = "新题 " + state.items.filter(i=>i.kind==="new").length +
    " · 复习 " + state.items.filter(i=>i.kind==="review").length +
    " · 预计 " + state.planned_minutes + " 分钟";
  $("#paceMeta").textContent = state.session_start + "–" + state.session_end;

  const warn = $("#warnBox");
  if(state.warnings && state.warnings.length){
    warn.classList.remove("hidden");
    warn.innerHTML = state.warnings.map(w => "⚠ " + esc(w)).join("<br>");
  } else { warn.classList.add("hidden"); }

  if(!selectedId && state.items.length){
    selectedId = (activeItem() || state.items.find(i => i.status !== "done") || state.items[0] || {}).id || null;
  }
  renderItems();
  renderTimer();
  renderRecent();
}

function renderItems(){
  const box = $("#items");
  if(!state.items.length){
    box.innerHTML = '<div class="empty">今天没有待办。可能已经全部完成，或计划还没生成。</div>';
    return;
  }
  box.innerHTML = state.items.map(i => {
    const st = STATUS[i.status] || STATUS.pending;
    const res = itemResult(i);
    const dot = i.status === "done" ? "done" : (i.status === "doing" ? "doing" : (i.status === "unfinished" ? "unfinished" : ""));
    const sub = [
      i.kind === "new" ? "新题" : "复习",
      i.group, i.difficulty,
      i.hints_used ? ("提示 " + i.hints_used + "/2") : "",
      i.viewed_reference ? "已看参考" : "",
      res && RESULT[res] ? RESULT[res][0] : ""
    ].filter(Boolean).join(" · ");
    return '<div class="item ' + i.status + (i.id === selectedId ? ' sel' : '') + '" data-id="' + i.id + '">' +
      '<div class="time">' + esc(i.planned_start) + '<span>' + esc(i.planned_end) + '</span></div>' +
      '<div class="dot ' + dot + '"></div>' +
      '<div><div class="ititle">' + esc(i.title) + '<em>#' + i.problem_id + '</em></div>' +
      '<div class="isub">' + esc(sub) + '</div></div>' +
      '<div><span class="pill ' + st[1] + '">' + st[0] + '</span></div>' +
      '</div>';
  }).join("");
  box.querySelectorAll(".item").forEach(el => {
    el.addEventListener("click", () => { selectedId = Number(el.dataset.id); renderItems(); renderTimer(); });
  });
}

function renderTimer(){
  const card = $("#timerCard");
  const i = currentItem();
  if(!i){ card.innerHTML = '<div class="empty">今天没有安排。可以在设置里重排计划，或直接去写题。</div>'; updateQuick(); return; }
  const st = STATUS[i.status] || STATUS.pending;
  const res = itemResult(i);
  const sess = i.session || {};
  const limit = (sess.limit_minutes || i.limit_minutes || (i.kind === "new" ? 25 : 15)) * 60;
  const started = parseDT(sess.started_at);
  const elapsed = sess.ended_at ? (sess.elapsed_sec || 0) : (started ? (Date.now() - started.getTime())/1000 : 0);
  const over = elapsed > limit;
  const extras = [
    i.kind === "new" ? "新题 25 分钟" : "复习 15 分钟",
    i.review_dates && i.review_dates.length ? ("待复习 " + i.review_dates.join(" / ")) : "",
    i.hints_used ? ("已用提示 " + i.hints_used + "/2") : "",
    i.viewed_reference ? "已看过参考题解" : ""
  ].filter(Boolean).join(" · ");

  let html = '<div class="thead"><div>' +
    '<span class="kicker">' + (i.id === state.current_item_id ? "正在计时" : "选中题目") + '</span>' +
    '<h2>#' + i.problem_id + ' ' + esc(i.title) + '</h2>' +
    '<div class="meta">' + esc(i.group) + ' · ' + esc(i.difficulty) + ' · ' + esc(i.planned_start) + '–' + esc(i.planned_end) + '</div>' +
    '</div><span class="pill ' + st[1] + '">' + st[0] + '</span></div>' +
    '<div class="clock' + (over ? " over" : "") + '"><b id="clockMain">' + fmtClock(elapsed) + '</b>' +
    '<span>' + (over ? "已超时 " : "已用时 / 上限 ") + fmtClock(limit) + '</span></div>' +
    '<div class="tbar' + (over ? " over" : "") + '"><i id="tbarFill" style="width:' + Math.min(100, elapsed*100/limit) + '%"></i></div>';

  if(i.status === "done" && res){
    html += '<div class="donebox"><b>' + (RESULT[res] ? RESULT[res][0] : "已完成") + '</b>' +
      ' · 用时 ' + minutes(sess.elapsed_sec || elapsed) + ' 分钟' +
      (i.note ? '<br>备注：' + esc(i.note) : '') + '</div>';
  } else if(i.status === "unfinished"){
    html += '<div class="donebox" style="background:rgba(248,113,113,.06);border-color:rgba(248,113,113,.25);color:#fecaca">' +
      '已标记未完成，明天会优先重新排入。<br>如果还想继续，可以重新开始计时。</div>';
  } else {
    html += '<div class="tip" style="margin-top:10px">' + esc(extras) + '</div>';
  }

  html += '<div class="actions">';
  if(i.status === "pending" || i.status === "unfinished"){
    html += '<button class="btn primary" data-act="start">开始计时</button>';
  }
  if(i.status !== "done"){
    html += '<button class="btn primary" data-act="code">写代码</button>';
    html += '<button class="btn" data-act="finish">完成本题</button>';
  }
  html += '<button class="btn ghost" data-act="statement">题面</button>';
  html += '<button class="btn ghost" data-act="hint">提示</button>';
  html += '<button class="btn ghost" data-act="reference">参考答案</button>';
  html += '<button class="btn ghost" data-act="check">运行用例</button>';
  html += '</div>';
  card.innerHTML = html;
  card.querySelectorAll("[data-act]").forEach(el => el.addEventListener("click", () => act(el.dataset.act, i)));
  updateQuick();
}

function updateQuick(){
  const has = !!currentItem();
  ["#btnCodeQuick","#btnStatementQuick","#btnHintQuick","#btnRefQuick"].forEach(s => { $(s).disabled = !has; });
}

function renderRecent(){
  const box = $("#recent");
  if(!state.recent || !state.recent.length){
    box.innerHTML = '<div class="empty">还没有记录。完成第一题后会出现在这里。</div>';
    return;
  }
  box.innerHTML = state.recent.map(r => {
    const rr = RESULT[r.result] || ["—","muted"];
    return '<div class="rrow"><div><span class="t">#' + r.problem_id + ' ' + esc(r.title) + '</span>' +
      ' <span class="m">' + rr[0] + '</span></div>' +
      '<div class="m">' + esc((r.day || "").slice(5)) + ' · ' + minutes(r.elapsed_sec) + ' 分钟</div></div>';
  }).join("");
}

function tick(){
  const i = currentItem();
  if(!i || !i.session || !i.session.started_at || i.session.ended_at) return;
  const limit = (i.session.limit_minutes || i.limit_minutes || 25) * 60;
  const start = parseDT(i.session.started_at);
  const elapsed = (Date.now() - start.getTime())/1000;
  const main = $("#clockMain"), fill = $("#tbarFill");
  if(main) main.textContent = fmtClock(elapsed);
  if(fill) fill.style.width = Math.min(100, elapsed*100/limit) + "%";
}

async function refresh(silent){
  if(busy) return;
  try{
    const data = await fetch("/api/state", {cache:"no-store"}).then(r => r.json());
    if(data.ok === false) throw new Error(data.error || "加载失败");
    state = data.state;
    lastRefresh = Date.now();
    if(selectedId && !state.items.some(i => i.id === selectedId)) selectedId = null;
    render();
  }catch(e){
    if(!silent) toast("连接训练器失败：" + e.message);
  }
}

function openModal(title, html, wide){
  $("#modalTitle").textContent = title;
  $("#modalBody").innerHTML = html;
  document.querySelector(".modal").classList.toggle("wide", !!wide);
  $("#overlay").classList.remove("hidden");
}
function closeModal(){
  $("#overlay").classList.add("hidden");
  document.querySelector(".modal").classList.remove("wide");
}
$("#modalClose").addEventListener("click", closeModal);
$("#overlay").addEventListener("mousedown", (e) => { if(e.target.id === "overlay") closeModal(); });
document.addEventListener("keydown", (e) => {
  if(e.key !== "Escape") return;
  if(!$("#overlay").classList.contains("hidden")){ closeModal(); return; }
  if(!$("#ws").classList.contains("hidden")) closeWorkspace();
});

async function act(kind, item){
  if(kind === "start") return startItem(item);
  if(kind === "finish") return openFinish(item);
  if(kind === "statement") return openStatement(item);
  if(kind === "hint") return openHint(item);
  if(kind === "reference") return openReference(item);
  if(kind === "check") return openWorkspace(item, true);
  if(kind === "code") return openWorkspace(item);
}

async function startItem(i){
  try{
    await api("/api/start", {item_id:i.id});
    toast("开始计时，专注这一题。");
    await refresh(true);
  }catch(e){ toast(e.message); }
}

function openFinish(i){
  const opts = [
    ["done","独立完成","没有看提示和参考题解"],
    ["hinted","借提示完成","看过提示，但自己写出来了"],
    ["rewritten","看题解后复现","看过参考，之后闭卷重写"],
    ["unfinished","未完成","明天优先重新安排"]
  ];
  const html = '<div class="tip" style="margin-bottom:10px">按真实情况标记。标记会决定复习间隔，也会影响明天的排题优先级。</div>' +
    '<div class="opt">' + opts.map((o,idx) =>
      '<label><input type="radio" name="res" value="' + o[0] + '"' + (idx===0?" checked":"") + '>' +
      o[1] + '<small>' + o[2] + '</small></label>').join("") + '</div>' +
    '<div class="field"><label>备注（可选）：卡在哪里、下次注意什么</label>' +
    '<textarea id="finishNote" rows="3" placeholder="例如：边界条件漏了，下次先想空数组"></textarea></div>' +
    '<div class="mfoot"><button class="btn" id="finishCancel">取消</button>' +
    '<button class="btn primary" id="finishSubmit">确认标记</button></div>';
  openModal("完成 #" + i.problem_id + " " + i.title, html);
  $("#finishCancel").onclick = closeModal;
  $("#finishSubmit").onclick = async () => {
    const result = document.querySelector('input[name="res"]:checked').value;
    const note = $("#finishNote").value.trim();
    try{
      const r = await api("/api/finish", {item_id:i.id, result, note});
      closeModal();
      toast("已记录：" + (RESULT[r.result] ? RESULT[r.result][0] : r.result));
      selectedId = i.id;
      await refresh(true);
    }catch(e){ toast(e.message); }
  };
}

async function openStatement(i){
  try{
    const data = await api("/api/statement?id=" + i.problem_id);
    openModal("#" + i.problem_id + " " + i.title, '<div class="md">' + data.html + '</div>');
  }catch(e){ toast(e.message); }
}

async function openHint(i){
  try{
    const data = await api("/api/hint", {problem_id:i.problem_id, level:1});
    showHint(i, data);
  }catch(e){ toast(e.message); }
}
function showHint(i, data){
  const more = data.level < data.total;
  const html = '<div class="hintbox">提示 ' + data.level + ' / ' + data.total + '<br><br>' + esc(data.hint) + '</div>' +
    '<div class="mfoot">' +
    (more ? '<button class="btn" id="hintMore">再给一条提示</button>' : '') +
    '<button class="btn ghost" id="hintRef">直接看参考题解</button>' +
    '<button class="btn primary" id="hintOk">知道了</button></div>';
  openModal("提示 · " + i.title, html);
  $("#hintOk").onclick = closeModal;
  if(more) $("#hintMore").onclick = async () => {
    try{
      const d = await api("/api/hint", {problem_id:i.problem_id, level:data.level + 1});
      showHint(i, d); refresh(true);
    }catch(e){ toast(e.message); }
  };
  $("#hintRef").onclick = () => openReference(i);
  refresh(true);
}

async function openReference(i){
  const gate = '<div class="gate"><b>先想清楚再看。</b>看参考题解会把这题记为“看题解后复现”，' +
    '1 天和 4 天后各复习一次。<br>建议先写一版能跑通思路的代码，再对照差距。</div>' +
    '<div class="mfoot"><button class="btn" id="refCancel">再想想</button>' +
    '<button class="btn danger" id="refOpen">打开参考题解</button></div>';
  openModal("参考答案 · " + i.title, gate);
  $("#refCancel").onclick = closeModal;
  $("#refOpen").onclick = async () => {
    try{
      const d = await api("/api/reference", {problem_id:i.problem_id});
      const html = '<div class="gate">已记录为看过参考。完成时请选择“看题解后复现”，并在明天闭卷重写一遍。</div>' +
        '<div style="display:flex;justify-content:flex-end;gap:8px;margin-bottom:9px">' +
        '<button class="btn ghost" id="copyRef">复制代码</button></div>' +
        '<pre class="code">' + esc(d.code) + '</pre>' +
        '<div class="mfoot"><button class="btn primary" id="refDone">关闭</button></div>';
      openModal("参考答案 · " + i.title, html);
      $("#refDone").onclick = closeModal;
      $("#copyRef").onclick = async () => {
        try{ await navigator.clipboard.writeText(d.code); toast("已复制"); }
        catch(e){ toast("复制失败，请手动选择"); }
      };
      refresh(true);
    }catch(e){ toast(e.message); }
  };
}

/* ---------------- 写代码工作台 ---------------- */
const ws = {
  pid:null, item:null, mode:"acm", dirty:false, cases:[], results:{}, best:{},
  file:"", errLine:0, pcTimer:null, saveTimer:null, pcSeq:0, running:false, resetArmed:false
};
const wsArea = $("#wsArea"), wsHl = $("#wsHl"), wsGutter = $("#wsGutter");

const PY_TOKEN = /(#[^\n]*)|("{3}[\s\S]*?(?:"{3}|$)|'{3}[\s\S]*?(?:'{3}|$)|"(?:\\.|[^"\\\n])*(?:"|$)|'(?:\\.|[^'\\\n])*(?:'|$))|\b(def|class|return|if|elif|else|for|while|in|not|and|or|is|import|from|as|with|try|except|finally|raise|yield|lambda|pass|break|continue|global|nonlocal|assert|del|async|await)\b|\b(None|True|False)\b|\b(print|len|range|enumerate|zip|map|filter|sorted|sum|min|max|abs|int|str|float|list|dict|set|tuple|bool|isinstance|getattr|setattr|hasattr|super|iter|next|reversed|any|all|divmod|pow|round|ord|chr|hex|bin|format|input|open|type|id|hash|callable|vars|dir|self)\b|(@[A-Za-z_]\w*)|\b(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?j?)\b|\b([A-Za-z_]\w*)(?=\s*\()/g;
function hl(code){
  let out = "", last = 0, m;
  PY_TOKEN.lastIndex = 0;
  while((m = PY_TOKEN.exec(code))){
    out += esc(code.slice(last, m.index));
    const cls = m[1]?"c":m[2]?"s":m[3]?"k":m[4]?"b":m[5]?"u":m[6]?"d":m[7]?"n":"f";
    out += '<span class="tk-' + cls + '">' + esc(m[0]) + "</span>";
    last = m.index + m[0].length;
    if(m[0].length === 0) PY_TOKEN.lastIndex++;
  }
  return out + esc(code.slice(last));
}
function edSync(){
  wsHl.scrollTop = wsArea.scrollTop; wsHl.scrollLeft = wsArea.scrollLeft;
  wsGutter.scrollTop = wsArea.scrollTop;
}
function edRender(){
  const code = wsArea.value;
  wsHl.innerHTML = hl(code) + "\n";
  const n = code.split("\n").length;
  let g = "";
  for(let i=1;i<=n;i++) g += "<div" + (i === ws.errLine ? ' class="err"' : "") + ">" + i + "</div>";
  wsGutter.innerHTML = g;
  edSync();
}
function edPos(){
  const upto = wsArea.value.slice(0, wsArea.selectionStart).split("\n");
  $("#wsPos").textContent = "行 " + upto.length + "，列 " + (upto[upto.length-1].length + 1) + " · 共 " + wsArea.value.split("\n").length + " 行";
}
function fireInput(){ wsArea.dispatchEvent(new Event("input")); }
function nowTime(){ return new Date().toLocaleTimeString("zh-CN", {hour12:false}); }

function setPc(cls, text){
  const el = $("#wsPc");
  el.className = "pcchip" + (cls ? " " + cls : "");
  el.innerHTML = "<i></i>" + esc(text);
}
function schedulePc(){
  clearTimeout(ws.pcTimer);
  setPc("busy", "预编译中…");
  ws.pcTimer = setTimeout(runPc, 400);
}
async function runPc(){
  const seq = ++ws.pcSeq;
  try{
    const d = (await api("/api/precompile", {code: wsArea.value})).compile;
    if(seq !== ws.pcSeq) return;
    if(d.ok){ ws.errLine = 0; setPc("ok", "已编译 · " + d.ms + "ms"); }
    else { ws.errLine = d.error.line || 0; setPc("err", "语法错误 · 第 " + d.error.line + " 行 " + d.error.msg); }
    edRender();
  }catch(e){ if(seq === ws.pcSeq) setPc("", "预编译不可用"); }
}
$("#wsPc").addEventListener("click", () => {
  if(!ws.errLine) return;
  const lines = wsArea.value.split("\n");
  let pos = 0;
  for(let i=0;i<Math.min(ws.errLine-1, lines.length);i++) pos += lines[i].length + 1;
  wsArea.focus();
  wsArea.setSelectionRange(pos, pos + (lines[ws.errLine-1]||"").length);
  wsArea.scrollTop = Math.max(0, (ws.errLine-4) * 21);
  edSync(); edPos();
});

async function flushSave(silent){
  clearTimeout(ws.saveTimer);
  if(!ws.pid || !ws.dirty) return true;
  try{
    const d = await api("/api/code", {problem_id:ws.pid, mode:ws.mode, code:wsArea.value});
    ws.dirty = false; ws.file = d.file;
    $("#wsFile").textContent = d.file;
    $("#wsSaveState").textContent = (silent ? "已自动保存 " : "已保存 ") + nowTime();
    return true;
  }catch(e){
    $("#wsSaveState").textContent = "保存失败：" + e.message;
    if(!silent) toast(e.message);
    return false;
  }
}
function scheduleSave(){
  clearTimeout(ws.saveTimer);
  ws.saveTimer = setTimeout(() => flushSave(true), 900);
}

function setModeButtons(){
  document.querySelectorAll("#wsModes button").forEach(b => b.classList.toggle("on", b.dataset.mode === ws.mode));
}
function loadCode(d){
  wsArea.value = d.code;
  ws.dirty = false; ws.file = d.file; ws.errLine = 0;
  $("#wsFile").textContent = d.file;
  $("#wsSaveState").textContent = "就绪 · 整份文件可删改";
  $("#wsModeDoc").textContent = ws.mode === "acm"
    ? "完整程序：main + 输入输出 + 全部辅助函数，均可删改"
    : "力扣签名：class Solution / 设计类，节点类可删改";
  edRender(); edPos(); renderResults(); schedulePc();
}
async function openWorkspace(i, autorun){
  ws.item = i; ws.pid = i.problem_id;
  ws.results = {}; ws.best = {}; ws.errLine = 0; ws.running = false;
  $("#ws").classList.remove("hidden");
  document.body.style.overflow = "hidden";
  $("#wsTitle").textContent = "#" + i.problem_id + " " + i.title;
  $("#wsDiff").textContent = i.difficulty || "";
  $("#wsMetrics").classList.add("hidden");
  $("#wsCases").innerHTML = '<div class="empty"><span class="spin"></span>正在加载代码与官方用例…</div>';
  setPc("", "预编译待命");
  try{
    const d = await api("/api/code?id=" + i.problem_id);
    ws.mode = d.mode; ws.cases = d.cases;
    if(d.best) ws.best[d.mode] = d.best;
    setModeButtons(); loadCode(d);
    wsArea.focus();
    if(autorun) wsRunAll();
  }catch(e){ toast(e.message); closeWorkspace(); }
}
async function switchMode(m){
  if(m === ws.mode || !ws.pid) return;
  await flushSave(true);
  try{
    const d = await api("/api/code?id=" + ws.pid + "&mode=" + m);
    ws.mode = m; ws.cases = d.cases;
    if(d.best) ws.best[m] = d.best;
    setModeButtons(); loadCode(d);
    wsArea.focus();
  }catch(e){ toast(e.message); }
}
document.querySelectorAll("#wsModes button").forEach(b =>
  b.addEventListener("click", () => switchMode(b.dataset.mode)));

async function closeWorkspace(){
  clearTimeout(ws.pcTimer);
  await flushSave(true);
  $("#ws").classList.add("hidden");
  document.body.style.overflow = "";
  ws.pid = null;
  refresh(true);
}
$("#wsBack").addEventListener("click", closeWorkspace);
$("#wsStatement").addEventListener("click", () => { if(ws.item) openStatement(ws.item); });
$("#wsSave").addEventListener("click", async () => { if(await flushSave(false)) toast("代码已保存"); });
$("#wsReset").addEventListener("click", async () => {
  const btn = $("#wsReset");
  if(!ws.resetArmed){
    ws.resetArmed = true;
    btn.textContent = "确认重置？"; btn.classList.add("danger");
    setTimeout(() => { ws.resetArmed = false; btn.textContent = "重置模板"; btn.classList.remove("danger"); }, 3000);
    return;
  }
  ws.resetArmed = false; btn.textContent = "重置模板"; btn.classList.remove("danger");
  try{
    const d = await api("/api/reset_code", {problem_id:ws.pid, mode:ws.mode});
    wsArea.value = d.code; ws.dirty = false;
    delete ws.results[ws.mode];
    edRender(); edPos(); renderResults(); schedulePc();
    $("#wsSaveState").textContent = "已重置为预生成模板";
    toast("已重置为预生成模板");
  }catch(e){ toast(e.message); }
});

function ringHtml(m){
  const pct = m.pass_rate, C = 2 * Math.PI * 34;
  const color = pct >= 100 ? "#4ade80" : pct >= 50 ? "#f5b64a" : "#f87171";
  return '<div class="ringbox"><svg viewBox="0 0 84 84" width="92" height="92">' +
    '<circle cx="42" cy="42" r="34" fill="none" stroke="#152540" stroke-width="8"/>' +
    '<circle cx="42" cy="42" r="34" fill="none" stroke="' + color + '" stroke-width="8" stroke-linecap="round" ' +
    'stroke-dasharray="' + (C * pct / 100).toFixed(1) + ' ' + C.toFixed(1) + '" transform="rotate(-90 42 42)"/>' +
    '<text x="42" y="40" text-anchor="middle" fill="' + color + '" font-size="16" font-weight="700">' + pct + '%</text>' +
    '<text x="42" y="55" text-anchor="middle" fill="#61748f" font-size="8.5">通过率</text></svg></div>';
}
function statsHtml(m){
  return '<div class="mgrid">' +
    '<div class="mcell ok"><b>' + m.passed + '</b><span>通过</span></div>' +
    '<div class="mcell warn"><b>' + m.failed + '</b><span>未通过</span></div>' +
    '<div class="mcell bad"><b>' + m.errors + '</b><span>错误</span></div>' +
    '<div class="mcell"><b>' + m.total + '</b><span>用例总数</span></div>' +
    '<div class="mcell wide"><b>' + m.total_ms + ' ms</b><span>总耗时 · 平均 ' + m.avg_ms + ' ms · 最大 ' + m.max_ms + ' ms</span></div>' +
    '</div>' + (m.interrupted ? '<div class="casenote">判题进程超时被终止，部分用例没有跑完。</div>' : '');
}
function caseRow(c, row){
  const st = row ? row.status : "official";
  const label = {pass:"通过", fail:"未通过", error:"运行错误", timeout:"超时", official:"官方用例"}[st] || st;
  const cls = {pass:"ok", fail:"warn", error:"bad", timeout:"bad", official:"info"}[st] || "muted";
  const input = row ? row.input : c.input;
  const expected = row ? row.expected : c.expected;
  const note = (row && row.note) || c.note || "";
  let body = '<div class="io"><label>输入</label><pre>' + esc(input) + '</pre></div>' +
    '<div class="io"><label>期望输出</label><pre>' + esc(expected) + '</pre></div>';
  if(row){
    body += '<div class="io"><label>你的输出</label><pre>' + esc(row.actual || "（无输出）") + '</pre></div>';
    if(row.detail) body += '<div class="casedetail">' + esc(row.detail) + '</div>';
  }
  if(note) body += '<div class="casenote">' + esc(note) + '</div>';
  return '<div class="case ' + (row ? (row.ok ? "good" : "bad") : "") + '">' +
    '<div class="casehead"><span>用例 ' + (c.index || "") + '<span class="pill ' + cls + '">' + label + '</span></span>' +
    '<span class="casems">' + (row ? row.ms + " ms" : "") + '</span></div>' +
    '<div class="casebody">' + body + '</div></div>';
}
function bindCases(){
  document.querySelectorAll("#wsCases .casehead").forEach(h =>
    h.addEventListener("click", () => h.parentElement.classList.toggle("open")));
}
function renderResults(){
  const r = ws.results[ws.mode];
  const best = ws.best[ws.mode];
  const bestEl = $("#wsBest");
  bestEl.textContent = best ? ("最佳 " + best.pass_rate + "% · 已运行 " + best.runs + " 次") : "尚未运行";
  bestEl.className = "pill " + (best ? (best.pass_rate >= 100 ? "ok" : "warn") : "muted");
  const box = $("#wsCases");
  if(!r){
    $("#wsMetrics").classList.add("hidden");
    box.innerHTML = '<div class="caseintro">官方用例 <b>' + ws.cases.length + '</b> 个 · 与力扣一致，一个不减。' +
      '点「运行全部用例」开始判题；展开任意用例可查看输入与期望输出。</div>' +
      ws.cases.map(c => caseRow(c, null)).join("");
    bindCases();
    return;
  }
  const m = r.metrics;
  const met = $("#wsMetrics");
  met.classList.remove("hidden");
  met.innerHTML = ringHtml(m) + statsHtml(m);
  box.innerHTML = r.results.map((row, idx) => caseRow(ws.cases[idx] || {index:row.index}, row)).join("");
  bindCases();
  const bad = box.querySelector(".case.bad");
  if(bad) bad.classList.add("open");
}
async function wsRunAll(){
  if(ws.running || !ws.pid) return;
  ws.running = true;
  const btn = $("#wsRun"), old = btn.innerHTML;
  btn.disabled = true; btn.innerHTML = '<span class="spin"></span>判题中…';
  $("#wsCases").innerHTML = '<div class="empty"><span class="spin"></span>正在隔离子进程里运行 ' +
    ws.cases.length + ' 个官方用例，最长约 30 秒…</div>';
  try{
    const d = await api("/api/run", {problem_id:ws.pid, mode:ws.mode, code:wsArea.value});
    ws.dirty = false;
    ws.results[ws.mode] = d;
    if(d.best) ws.best[ws.mode] = d.best;
    $("#wsSaveState").textContent = "已保存 · 判题完成 " + nowTime();
    renderResults();
    const m = d.metrics;
    toast(m.passed === m.total
      ? "全部通过 " + m.passed + "/" + m.total + " · 总耗时 " + m.total_ms + "ms"
      : "通过 " + m.passed + "/" + m.total + " · 通过率 " + m.pass_rate + "%");
  }catch(e){
    toast(e.message);
    renderResults();
  }finally{
    ws.running = false; btn.disabled = false; btn.innerHTML = old;
  }
}
$("#wsRun").addEventListener("click", wsRunAll);

wsArea.addEventListener("input", () => {
  ws.dirty = true;
  $("#wsSaveState").textContent = "有未保存改动";
  edRender(); edPos(); scheduleSave(); schedulePc();
});
wsArea.addEventListener("scroll", edSync);
wsArea.addEventListener("keyup", edPos);
wsArea.addEventListener("click", edPos);
wsArea.addEventListener("keydown", (e) => {
  const ta = wsArea, v = ta.value, s = ta.selectionStart, en = ta.selectionEnd;
  if(e.key === "Tab"){
    e.preventDefault();
    const ls = v.lastIndexOf("\n", s - 1) + 1;
    if(s !== en && v.slice(s, en).includes("\n")){
      const le = v.indexOf("\n", en);
      const end = le === -1 ? v.length : le;
      const out = v.slice(ls, end).split("\n")
        .map(l => e.shiftKey ? l.replace(/^ {1,4}/, "") : "    " + l).join("\n");
      ta.setRangeText(out, ls, end, "select");
    } else if(e.shiftKey){
      const m = v.slice(ls).match(/^ {1,4}/);
      if(m) ta.setRangeText("", ls, ls + m[0].length, "end");
    } else {
      ta.setRangeText("    ", s, en, "end");
    }
    fireInput();
  } else if(e.key === "Enter"){
    e.preventDefault();
    const ls = v.lastIndexOf("\n", s - 1) + 1;
    const line = v.slice(ls, s);
    const indent = (line.match(/^[ \t]*/) || [""])[0];
    const extra = /:\s*$/.test(line) ? "    " : "";
    ta.setRangeText("\n" + indent + extra, s, en, "end");
    fireInput();
  } else if((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s"){
    e.preventDefault();
    flushSave(false).then(ok => { if(ok) toast("代码已保存"); });
  } else if((e.ctrlKey || e.metaKey) && e.key === "Enter"){
    e.preventDefault();
    wsRunAll();
  }
});

function openSettings(){
  const c = state.config || {};
  const html = '<div class="grid2">' +
    '<div class="field"><label>截止日期</label><input id="cfgDeadline" type="date" value="' + esc(c.deadline) + '"></div>' +
    '<div class="field"><label>每日新题上限</label><input id="cfgMaxNew" type="number" min="1" max="12" value="' + c.max_new_per_day + '"></div>' +
    '<div class="field"><label>练习开始</label><input id="cfgStart" type="time" value="' + esc(c.session_start) + '"></div>' +
    '<div class="field"><label>练习结束</label><input id="cfgEnd" type="time" value="' + esc(c.session_end) + '"></div>' +
    '<div class="field"><label>新题分钟数</label><input id="cfgNewMin" type="number" min="5" max="60" value="' + c.new_slot_minutes + '"></div>' +
    '<div class="field"><label>复习分钟数</label><input id="cfgRevMin" type="number" min="5" max="45" value="' + c.review_slot_minutes + '"></div>' +
    '<div class="field"><label>每日复习上限</label><input id="cfgMaxRev" type="number" min="0" max="5" value="' + c.max_reviews_per_day + '"></div>' +
    '<div class="field"><label>仪表盘端口（重启生效）</label><input id="cfgPort" type="number" min="1024" max="65535" value="' + c.port + '"></div>' +
    '</div>' +
    '<label class="check"><input id="cfgNotify" type="checkbox"' + (c.notify ? " checked":"") + '>桌面提醒</label>' +
    '<label class="check"><input id="cfgOpen" type="checkbox"' + (c.open_dashboard ? " checked":"") + '>开始时自动打开仪表盘</label>' +
    '<div class="tip" style="margin-top:8px">改截止日期或时段后，点“保存并重排今日”，会把今天还没开始的题按新配置重新排。</div>' +
    '<div class="mfoot"><button class="btn" id="cfgCancel">取消</button>' +
    '<button class="btn primary" id="cfgSave">保存并重排今日</button></div>';
  openModal("设置", html);
  $("#cfgCancel").onclick = closeModal;
  $("#cfgSave").onclick = async () => {
    const body = {
      deadline: $("#cfgDeadline").value,
      max_new_per_day: Number($("#cfgMaxNew").value),
      session_start: $("#cfgStart").value,
      session_end: $("#cfgEnd").value,
      new_slot_minutes: Number($("#cfgNewMin").value),
      review_slot_minutes: Number($("#cfgRevMin").value),
      max_reviews_per_day: Number($("#cfgMaxRev").value),
      port: Number($("#cfgPort").value),
      notify: $("#cfgNotify").checked,
      open_dashboard: $("#cfgOpen").checked
    };
    try{
      await api("/api/config", body);
      try{ await api("/api/replan", {}); }catch(e){ toast("设置已保存；" + e.message); }
      closeModal(); toast("设置已保存"); await refresh(true);
    }catch(e){ toast(e.message); }
  };
}

async function replan(){
  if(!confirm("按当前设置重排今天还没开始的题目？已开始或已完成的题不会动。")) return;
  try{ await api("/api/replan", {}); toast("已重排"); await refresh(true); }
  catch(e){ toast(e.message); }
}

$("#btnSettings").addEventListener("click", openSettings);
$("#btnReplan").addEventListener("click", replan);
$("#btnStatementQuick").addEventListener("click", () => { const i = currentItem(); if(i) openStatement(i); });
$("#btnCodeQuick").addEventListener("click", () => { const i = currentItem(); if(i) openWorkspace(i); });
$("#btnHintQuick").addEventListener("click", () => { const i = currentItem(); if(i) openHint(i); });
$("#btnRefQuick").addEventListener("click", () => { const i = currentItem(); if(i) openReference(i); });

refresh();
setInterval(tick, 1000);
setInterval(() => { if(Date.now() - lastRefresh > 3500 && !busy) refresh(true); }, 4000);
</script>
</body>
</html>
"""


def page() -> str:
    return PAGE
