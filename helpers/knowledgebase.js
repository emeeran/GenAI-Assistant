const fs = require('fs').promises;
const path = require('path');
const kbPath = path.join(__dirname, '..', 'data', 'knowledgebase.json');

async function readKnowledgeBase() {
  try {
    const data = await fs.readFile(kbPath, 'utf-8');
    return JSON.parse(data);
  } catch (err) {
    // If file does not exist or other error, return default
    return { files: [] };
  }
}

async function updateKnowledgeBase(newFiles) {
  const kb = await readKnowledgeBase();
  kb.files = kb.files.concat(newFiles);
  await fs.writeFile(kbPath, JSON.stringify(kb, null, 2));
  return kb;
}

module.exports = { readKnowledgeBase, updateKnowledgeBase };
