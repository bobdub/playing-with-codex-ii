window.__GARDEN_CONFIG = window.__GARDEN_CONFIG || {
  tagging: {
    // caretakers can adjust these defaults without touching core logic
    maxTags: 5,
    ngramRange: [1, 2],
    enableSynonyms: true,
    weighting: {
      base: 1,
      lengthBonus: 0.05,
      positionDecay: 0.05,
      ngramMultiplier: 1.2,
      synonymMultiplier: 0.9,
    },
    synonyms: {
      welcome: ["greeting", "introduction"],
      caretaker: ["gardener", "steward"],
      seed: ["sprout", "teaching"],
    },
  },
};
