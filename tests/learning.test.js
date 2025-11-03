import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';

function createGardenHarness() {
  const source = readFileSync(new URL('../docs/app.js', import.meta.url), 'utf8');
  const sanitized = source.replace(/export\s+\{[\s\S]*?\};?\s*$/, '');
  const context = {
    console,
    window: undefined,
    document: undefined,
    localStorage: undefined,
    crypto,
  };
  vm.createContext(context);
  vm.runInContext(sanitized, context);
  return {
    eval(script) {
      return vm.runInContext(script, context);
    },
  };
}

test('natural conversation learning engages when no strong seed match exists', () => {
  const garden = createGardenHarness();
  garden.eval("state.seeds.push({ id: 'seed-1', prompt: 'unrelated topic', response: 'unrelated answer' })");

  garden.eval("addMessage('user', 'How do I nurture the sprouts?', buildUserMeta('How do I nurture the sprouts?', 60))");
  garden.eval("addMessage('garden', 'Acknowledged', {})");
  garden.eval("addMessage('user', 'What rituals keep the garden calm?', buildUserMeta('What rituals keep the garden calm?', 60))");
  garden.eval("addMessage('garden', 'Working on it', {})");
  garden.eval("addMessage('user', 'Can you stay with these themes?', buildUserMeta('Can you stay with these themes?', 60))");

  const reply = garden.eval("synthesizeResponse('Can you stay with these themes?', 60)");
  assert.equal(reply.meta.strategy, 'learned');
  assert.match(reply.text, /I'm weaving them together/i);
});
