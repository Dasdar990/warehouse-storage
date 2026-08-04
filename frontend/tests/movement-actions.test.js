import test from 'node:test';
import assert from 'node:assert/strict';

import { getMovementActionLabel } from '../utils/movementActions.js';

test('edit movements render with an explicit label', () => {
  assert.equal(getMovementActionLabel('edit'), 'Edited');
});
