export interface StoryAsset {
  name: string;
  image: any; // Image require path
}

export class Story {
  id: string;
  storyTitle: string;
  background: StoryAsset;
  character: StoryAsset;
  theme: StoryAsset;
  keyItems: StoryAsset[];
  generatedStory?: string;

  constructor(
    id: string,
    storyTitle: string = "Untitled Story",
    background: StoryAsset = { name: "", image: null },
    character: StoryAsset = { name: "", image: null },
    theme: StoryAsset = { name: "", image: null },
    keyItems: StoryAsset[] = []
  ) {
    this.id = id;
    this.storyTitle = storyTitle;
    this.background = background;
    this.character = character;
    this.theme = theme;
    this.keyItems = keyItems;
  }

  generateStory(promptTemplate: string = ""): string {
    // This method will use LLM to generate story with the properties
    // For now, return a placeholder until backend implementation
    const defaultTemplate = `
Create an adventure story with the following elements:
- Title: ${this.storyTitle}
- Background: ${this.background.name}
- Character: ${this.character.name}
- Theme: ${this.theme.name}
- Key Items: ${this.keyItems.map(item => item.name).join(', ')}

Generate an engaging story that incorporates all these elements.
    `.trim();

    const template = promptTemplate || defaultTemplate;

    // Placeholder for LLM integration
    this.generatedStory = `Generated story for "${this.storyTitle}" with ${this.character.name} in ${this.background.name} setting...`;

    return this.generatedStory;
  }

  toJSON() {
    return {
      id: this.id,
      storyTitle: this.storyTitle,
      background: this.background,
      character: this.character,
      theme: this.theme,
      keyItems: this.keyItems,
      generatedStory: this.generatedStory
    };
  }

  static fromJSON(json: any): Story {
    const story = new Story(
      json.id,
      json.storyTitle,
      json.background,
      json.character,
      json.theme,
      json.keyItems
    );
    story.generatedStory = json.generatedStory;
    return story;
  }
}