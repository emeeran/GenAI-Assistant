require('dotenv').config();
const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

// ...existing code...

// Use separated route files
const uploadRouter = require('./routes/upload');
const filesRouter = require('./routes/files');

app.use('/upload', uploadRouter);
app.use('/files', filesRouter);

// ...existing code...
app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
