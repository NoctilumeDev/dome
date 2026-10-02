import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame, matchesGuess, normalizeGuess, roundScore } from '../static/game.mjs';
import { puzzles } from '../static/puzzles.mjs';
test('20 unique puzzles contain complete drawings, hints and accepted answers', () => {
  assert.equal(new Set(puzzles.map((p) => p.id)).size, 20);
  for (const p of puzzles) {
    assert.ok(p.strokes.length >= 3);
    assert.equal(p.hints.length, 2);
    assert.ok(matchesGuess(p, p.answer));
    for (const alias of p.aliases) assert.ok(matchesGuess(p, alias));
    assert.equal(matchesGuess(p, ''), false);
  }
});
test('Chinese and English guesses normalize without accepting substring guesses', () => {
  const p = puzzles.find((p) => p.id === 'icecream');
  assert.ok(matchesGuess(p, ' ＩＣＥ　ＣＲＥＡＭ！ '));
  assert.equal(normalizeGuess('雨 伞。'), '雨伞');
  assert.equal(matchesGuess(p, 'ice'), false);
  assert.equal(matchesGuess(p, '我觉得是冰淇淋'), false);
});
test('wrong guesses do not finish a round; scoring applies hints once and resolves once', () => {
  const g = createGame(puzzles, () => 0.5);
  g.start();
  assert.equal(g.total, 5);
  assert.equal(g.guess('not the answer', 30), false);
  assert.equal(g.next(), false);
  assert.ok(g.hint());
  assert.ok(g.hint());
  assert.equal(g.hint(), null);
  const result = g.guess(g.current.answer, 30);
  assert.equal(result.score, 30);
  assert.equal(g.resolve('skip'), null);
  assert.equal(g.guess(g.current.answer, 20), null);
  assert.equal(g.results.length, 1);
  assert.ok(g.next());
  assert.equal(g.hints, 0);
  assert.equal(g.resolved, false);
});
test('skip and timeout score zero; five rounds contain no duplicate puzzles; replay resets', () => {
  const g = createGame(puzzles);
  g.start();
  const ids = new Set();
  do {
    ids.add(g.current.id);
    g.resolve(g.number % 2 ? 'skip' : 'timeout');
  } while (g.next());
  assert.equal(ids.size, 5);
  assert.equal(g.results.length, 5);
  assert.equal(g.score, 0);
  assert.equal(g.next(), false);
  g.start();
  assert.equal(g.number, 1);
  assert.equal(g.results.length, 0);
  assert.equal(roundScore(60, 0), 100);
  assert.equal(roundScore(0, 2), 20);
});
