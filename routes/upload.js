const express = require('express');
const multer  = require('multer');
const fs = require('fs').promises;
const path = require('path');
const { updateKnowledgeBase } = require('../helpers/knowledgebase');
const router = express.Router();

// Configure Multer with file size limit, etc.
const upload = multer({
  dest: path.join(__dirname, '..', 'uploads'),
  limits: { fileSize: 5 * 1024 * 1024 } // 5MB limit
});

router.post('/', upload.array('files'), async (req, res) => {
  try {
    if (!req.files || req.files.length === 0) {
      return res.status(400).send('No files were uploaded.');
    }
    const newFiles = await Promise.all(req.files.map(async file => {
      // Read file content asynchronously
      const fileContent = await fs.readFile(file.path, 'utf-8');
      // Clean up temp file
      await fs.unlink(file.path);
      return {
        originalName: file.originalname,
        content: fileContent,
        uploadDate: new Date().toISOString()
      };
    }));
    await updateKnowledgeBase(newFiles);
    res.send('Files uploaded and processed successfully.');
  } catch (err) {
    console.error(err);
    res.status(500).send('Server error processing files.');
  }
});

module.exports = router;
