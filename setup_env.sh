#!/bin/bash
# Setup script for environment variables

echo "Setting up environment variables..."
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "OPENAI_API_KEY=YOUR_KEY_HERE" > .env
    echo ".env file created successfully!"
else
    echo ".env file already exists. Skipping..."
fi

echo ""
echo "Setup complete!"
echo "⚠️  Remember: Never commit .env file to Git!"
