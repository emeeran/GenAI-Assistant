const express = require('express');
const { readKnowledgeBase } = require('../helpers/knowledgebase');
const router = express.Router();

router.get('/', async (req, res) => {
  try {
    const kb = await readKnowledgeBase();
    res.json(kb);
  } catch (err) {
    console.error(err);
    res.status(500).send('Server error retrieving files.');
  }
});

module.exports = router;
