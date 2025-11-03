import test from 'node:test';
import assert from 'node:assert/strict';

import {
  scoreIntentProbabilities,
  computeIntentAlignment,
  computeTagAlignment,
  jaccardSimilarity,
  deriveTags,
  normalizeTagCollection,
  INTENT_CLASSES,
  shouldUseWordEcho,
} from '../docs/app.js';

test('scoreIntentProbabilities emphasizes inquiry prompts', () => {
  const profile = scoreIntentProbabilities('How do we welcome new caretakers?', []);
  assert.equal(profile.intent, 'inquiry');
  assert.ok(profile.probabilities.inquiry > 0.4);
  const total = Object.values(profile.probabilities).reduce((sum, value) => sum + value, 0);
  assert.ok(Math.abs(total - 1) < 0.05);
});

test('planning signals from metatags increase planning confidence', () => {
  const tags = normalizeTagCollection([
    { term: 'roadmap', weight: 2 },
    { term: 'plan', weight: 1.5 },
  ]);
  const profile = scoreIntentProbabilities('Draft the milestones for our release phases.', tags);
  assert.equal(profile.intent, 'planning');
  assert.ok(profile.probabilities.planning > profile.probabilities.signal);
});

test('computeIntentAlignment returns dot product across intents', () => {
  const user = { probabilities: { inquiry: 0.6, planning: 0.2, reflection: 0.1, signal: 0.1 } };
  const seed = { probabilities: { inquiry: 0.5, planning: 0.4, reflection: 0.05, signal: 0.05 } };
  const alignment = computeIntentAlignment(user, seed);
  const expected = 0.6 * 0.5 + 0.2 * 0.4 + 0.1 * 0.05 + 0.1 * 0.05;
  assert.equal(Number(alignment.toFixed(6)), Number(expected.toFixed(6)));
});

test('computeTagAlignment balances shared weights', () => {
  const userTags = [
    { term: 'welcome', weight: 1 },
    { term: 'onboarding', weight: 2 },
  ];
  const seedTags = [
    { term: 'welcome', weight: 0.5 },
    { term: 'ritual', weight: 1 },
  ];
  const alignment = computeTagAlignment(userTags, seedTags);
  assert.ok(alignment > 0);
  assert.ok(alignment < 1);
});

test('jaccardSimilarity favors overlapping tokens', () => {
  const a = ['garden', 'metrics', 'intent'];
  const b = ['metrics', 'intent', 'telemetry'];
  const value = jaccardSimilarity(a, b);
  assert.equal(value, 2 / 4);
});

test('deriveTags extracts weighted keywords and phrases', () => {
  const tags = deriveTags('Plan radiant welcome rituals for new caretakers');
  const tagTerms = tags.map((tag) => tag.term);
  assert.ok(tagTerms.some((term) => term.includes('plan')));
  assert.ok(tagTerms.some((term) => term.includes('welcome')));
});

test('intent classes remain complete', () => {
  assert.deepEqual(INTENT_CLASSES.sort(), ['inquiry', 'planning', 'reflection', 'signal'].sort());
});

test('shouldUseWordEcho returns true for identical learned word seeds', () => {
  const seed = { prompt: 'Hello', response: 'hello' };
  assert.equal(shouldUseWordEcho(seed, 'hello', { jaccard: 1 }), true);
});

test('shouldUseWordEcho rejects non-matching or multiword seeds', () => {
  const multiwordSeed = { prompt: 'hello there', response: 'hello there' };
  assert.equal(shouldUseWordEcho(multiwordSeed, 'hello there', { jaccard: 1 }), false);

  const mismatchSeed = { prompt: 'hello', response: 'hola' };
  assert.equal(shouldUseWordEcho(mismatchSeed, 'hello', { jaccard: 1 }), false);

  const lowMatchSeed = { prompt: 'hello', response: 'hello' };
  assert.equal(shouldUseWordEcho(lowMatchSeed, 'hello', { jaccard: 0.8 }), false);
});
