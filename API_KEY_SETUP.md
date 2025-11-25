# Setting Up Your API Key

## Quick Setup (2 steps)

### Step 1: Get your API key
1. Go to https://aistudio.google.com/apikey
2. Click "Create API Key"
3. Copy the key (it will look like `AIzaSy...`)

### Step 2: Add it to the .env file
Open the `.env` file in this directory and replace `your-api-key-here` with your actual API key:

```
GOOGLE_API_KEY=AIzaSy...your-actual-key-here
```

That's it! The application will now automatically load your API key from the `.env` file.

## Security Notes

✅ **Safe**: The `.env` file is already in `.gitignore`, so it won't be pushed to GitHub  
✅ **Template**: The `.env.example` file shows the format without exposing your key  
✅ **Automatic**: All agents will automatically load the key from `.env`

## Testing

After adding your API key, test it works:

```bash
# Test the AnalystAgent
.venv/bin/python test_analyst.py

# Run the full evaluation suite
.venv/bin/python -m evals.eval_runner
```

## Troubleshooting

**If you see "API key not valid":**
- Make sure you copied the entire key (no spaces or newlines)
- Verify the key is active at https://aistudio.google.com/apikey
- Check that the `.env` file has no quotes around the key value
