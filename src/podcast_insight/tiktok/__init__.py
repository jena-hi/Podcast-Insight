"""TikTok layer: turn each episode's top topics into 15s branded video specs.

The codebase produces the deterministic, on-brand pieces — a 15-second scene
storyboard, a voiceover script, and a caption in the Unscripted Intelligence
voice. The actual video is rendered + exported via the Canva connector in a
Claude session (see CLAUDE.md / docs/TIKTOK.md). Optional TTS can synthesize the
voiceover audio if a provider is configured.
"""
