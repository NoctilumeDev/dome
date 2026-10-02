import { puzzles } from './puzzles.mjs';
import { createGame, ROUND_SECONDS } from './game.mjs';
const $ = (id) => document.getElementById(id);
const game = createGame(puzzles),
  namespace = 'http://www.w3.org/2000/svg';
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
let remaining = ROUND_SECONDS,
  timer = null,
  lastTick = 0,
  drawingAnimations = [],
  running = false;
if (location.pathname.includes('/dianjing/')) {
  $('projects-link').href = '../index.html';
  $('projects-link').textContent = '← 项目列表';
}
function screen(id) {
  for (const name of ['welcome', 'playing', 'finished']) $(name).hidden = name !== id;
}
function stopTimer() {
  clearInterval(timer);
  timer = null;
}
function tick() {
  const now = performance.now();
  if (document.hidden) {
    lastTick = now;
    return;
  }
  remaining = Math.max(0, remaining - (now - lastTick) / 1000);
  lastTick = now;
  $('timer-label').textContent = Math.ceil(remaining) + ' 秒';
  $('timer-fill').style.width = (remaining / ROUND_SECONDS) * 100 + '%';
  if (!remaining) resolve(game.resolve('timeout'));
}
document.addEventListener('visibilitychange', () => {
  lastTick = performance.now();
});
function draw() {
  drawingAnimations.forEach((animation) => animation.cancel());
  drawingAnimations = [];
  const svg = $('drawing');
  svg.replaceChildren();
  svg.classList.remove('completed');
  const group = document.createElementNS(namespace, 'g');
  for (const [name, value] of Object.entries({
    stroke: 'currentColor',
    'stroke-width': 5,
    'stroke-linecap': 'round',
    'stroke-linejoin': 'round',
    fill: 'none',
  }))
    group.setAttribute(name, value);
  svg.append(group);
  game.current.strokes.forEach((stroke, i) => {
    const node = document.createElementNS(namespace, stroke.tag);
    for (const [key, value] of Object.entries(stroke))
      if (key !== 'tag') node.setAttribute(key, value);
    group.append(node);
    if (!reducedMotion) {
      const length = node.getTotalLength();
      node.style.strokeDasharray = length;
      drawingAnimations.push(
        node.animate([{ strokeDashoffset: length }, { strokeDashoffset: 0 }], {
          duration: 850,
          delay: i * 730,
          fill: 'both',
          easing: 'ease-in-out',
        })
      );
    }
  });
  svg.setAttribute('aria-label', '待猜图画，类别：' + game.current.category);
}
function dots() {
  $('round-dots').replaceChildren();
  for (let i = 0; i < game.total; i++) {
    const dot = document.createElement('i');
    if (game.results[i]?.status === 'correct') dot.className = 'correct';
    else if (i === game.number - 1) dot.className = 'active';
    $('round-dots').append(dot);
  }
}
function round() {
  stopTimer();
  running = true;
  remaining = ROUND_SECONDS;
  lastTick = performance.now();
  document.body.classList.add('play-active');
  screen('playing');
  $('guess').value = '';
  $('guess').disabled = false;
  $('submit').disabled = false;
  $('guess-form').hidden = false;
  $('tools').hidden = false;
  $('next').hidden = true;
  $('hint').disabled = false;
  $('hints').replaceChildren();
  $('feedback').textContent = '';
  $('feedback').className = 'feedback';
  $('category').textContent = game.current.category;
  $('answer-length').textContent = `中文答案 ${
    [...game.current.answer].length
  } 个字，也可以用英文。`;
  $('score').textContent = game.score;
  $('round-label').textContent = `第 ${game.number} / ${game.total} 幅`;
  $('drawing-label').textContent = '正在画，慢慢看';
  $('canvas-caption').textContent = '不用急，下一笔可能就是线索。';
  $('guess-title').textContent = '这一幅，你看懂了吗？';
  dots();
  draw();
  tick();
  timer = setInterval(tick, 150);
  if (matchMedia('(max-width: 680px)').matches)
    document
      .querySelector('.canvas-card')
      .scrollIntoView({ block: 'start', behavior: reducedMotion ? 'auto' : 'smooth' });
}
function start() {
  game.start();
  round();
}
function resolve(result) {
  if (!result) return;
  stopTimer();
  running = false;
  drawingAnimations.forEach((animation) => animation.finish());
  $('drawing').classList.add('completed');
  $('drawing').setAttribute('aria-label', '答案图画：' + result.answer);
  $('drawing-label').textContent = '这一幅，完成了';
  $('canvas-caption').textContent = result.answer;
  $('guess-title').textContent = result.status === 'correct' ? '对，就是它！' : '这幅画想说的是…';
  $('feedback').textContent =
    result.status === 'correct'
      ? `猜对了「${result.answer}」，+${result.score} 分！`
      : `${result.status === 'timeout' ? '时间到' : '先放过这幅'}，答案是「${result.answer}」。`;
  $('feedback').className = 'feedback' + (result.status === 'correct' ? ' success' : '');
  $('guess').disabled = true;
  $('submit').disabled = true;
  $('tools').hidden = true;
  $('next').hidden = false;
  $('next').textContent = game.number === game.total ? '看看这局成绩 →' : '下一幅 →';
  $('score').textContent = game.score;
  dots();
}
$('guess-form').addEventListener('submit', (event) => {
  event.preventDefault();
  if (!running) return;
  const value = $('guess').value.trim();
  if (!value) {
    $('feedback').textContent = '先写下你的猜想。';
    return;
  }
  tick();
  if (!running) return;
  const result = game.guess(value, remaining);
  if (result) resolve(result);
  else {
    $('feedback').textContent = '还差一点，再看看接下来的线索。';
    $('guess').select();
  }
});
$('guess').addEventListener('keydown', (event) => {
  if (event.isComposing && event.key === 'Enter') event.preventDefault();
});
$('hint').addEventListener('click', () => {
  const hint = game.hint();
  if (hint) {
    const p = document.createElement('p');
    p.textContent = `提示 ${game.hints}：${hint}`;
    $('hints').append(p);
  }
  $('hint').disabled = game.hints >= game.current.hints.length;
});
$('skip').addEventListener('click', () => resolve(game.resolve('skip')));
$('next').addEventListener('click', () => {
  if (game.next()) round();
  else finish();
});
function finish() {
  stopTimer();
  screen('finished');
  const correct = game.results.filter((r) => r.status === 'correct').length;
  $('finish-title').textContent = `你为 ${correct} 幅画点了睛。`;
  $('final-score').textContent = game.score;
  let best = game.score;
  try {
    best = Math.max(Number(localStorage.getItem('dianjing-best-v1')) || 0, game.score);
    localStorage.setItem('dianjing-best-v1', best);
  } catch (_) {
    /* Play remains available without storage. */
  }
  $('best-score').textContent = `这个浏览器的最高分：${best}。再来一局？`;
  $('results').replaceChildren();
  game.results.forEach((result, i) => {
    const li = document.createElement('li'),
      label = document.createElement('b'),
      value = document.createElement('span');
    label.textContent = `${i + 1}. ${result.answer}`;
    value.textContent =
      result.status === 'correct'
        ? `猜对 · ${result.score} 分`
        : result.status === 'timeout'
        ? '时间到'
        : '跳过';
    li.append(label, value);
    $('results').append(li);
  });
  $('drawing-label').textContent = '五幅画，一次小冒险';
  $('round-label').textContent = '这局完成';
  $('timer-label').textContent = '再见，下一幅画';
}
$('start').addEventListener('click', start);
$('restart').addEventListener('click', start);
