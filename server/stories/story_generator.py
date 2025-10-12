"""
Story generation service with template-based and LLM-based generation.
"""
import random
from django.conf import settings


# Story templates organized by theme
STORY_TEMPLATES = {
    'caring': [
        {
            'title': '{name} and the Lost Puppy',
            'template': """Once upon a time, there was a kind {age}-year-old named {name}. One sunny day, {name} heard a soft whimpering sound coming from the park. Following the sound, {name} discovered a tiny puppy hiding under a bench, looking scared and alone.

{name} gently approached the puppy, speaking in a soft voice. "Don't worry, little one. I'll help you find your home." {name} carefully picked up the puppy and noticed it had a collar with a phone number.

With the help of a grown-up, {name} called the number. Soon, a worried family arrived, so happy to see their lost puppy! They thanked {name} for being so caring and gentle.

The puppy's family invited {name} to visit anytime. {name} learned that being caring and helping others can create wonderful friendships.

The End."""
        },
        {
            'title': '{name}\'s Garden of Kindness',
            'template': """In a cheerful neighborhood lived {name}, a {age}-year-old who loved plants and flowers. One day, {name} noticed that the neighborhood garden looked sad and overgrown.

{name} had an idea! "I'll help make the garden beautiful again!" With permission from the grown-ups, {name} started pulling weeds and watering the thirsty plants.

Soon, neighbors noticed {name}'s hard work. They joined in, and together they planted colorful flowers, tomatoes, and herbs. The garden transformed into a beautiful space where everyone could enjoy nature.

{name} felt proud seeing neighbors gathering in the garden, sharing vegetables, and making new friends. The garden became a special place because {name} showed how one caring person can make a big difference.

The End."""
        }
    ],
    'courage': [
        {
            'title': '{name} and the Dark Cave',
            'template': """Deep in the forest stood a mysterious cave that everyone was afraid to explore. But brave {name}, who was {age} years old, was curious about what might be inside.

One day, with a flashlight and a trusted friend, {name} decided to be brave. "We can do this together," {name} said. Step by step, they walked into the dark cave, their hearts beating fast.

Inside, instead of something scary, they discovered beautiful crystal formations that sparkled like stars! The cave was full of natural wonders that no one had ever seen before.

{name} realized that being courageous doesn't mean not being scared—it means doing something even when you ARE scared. The discovery brought joy to the whole village, and {name} became known as the brave explorer.

The End."""
        }
    ],
    'friendship': [
        {
            'title': '{name} and the New Friend',
            'template': """At school, {name}, who was {age} years old, noticed a new student sitting alone at lunch. The new student looked lonely and shy.

{name} remembered what it felt like to be new and made a brave decision. Walking over with a big smile, {name} said, "Hi! Would you like to sit with me and my friends?"

The new student's face lit up with happiness. They talked about their favorite games, books, and hobbies. {name} discovered they had so much in common!

From that day on, they became the best of friends. {name} learned that friendship starts with one kind gesture, and being friendly can change someone's whole day. Making a new friend made {name}'s days even more fun and special.

The End."""
        }
    ],
    'honest': [
        {
            'title': '{name} Tells the Truth',
            'template': """One afternoon, {age}-year-old {name} accidentally broke a special vase while playing indoors. {name}'s heart sank. No one had seen what happened, and {name} was scared of getting in trouble.

{name} thought about hiding the broken pieces, but something didn't feel right. Taking a deep breath, {name} decided to be honest and tell the truth, even though it was scary.

"I'm sorry," {name} said, showing the broken pieces. "I was playing and accidentally broke the vase. I should have been more careful."

To {name}'s surprise, the grown-ups were proud of {name} for being honest. "Everyone makes mistakes," they said. "But telling the truth takes real courage. We're proud of you."

{name} learned that being honest, even when it's hard, is always the right choice. It makes others trust you and makes you feel good inside.

The End."""
        }
    ],
    'nature': [
        {
            'title': '{name}\'s Forest Adventure',
            'template': """One beautiful morning, {name}, a curious {age}-year-old, went on a nature walk in the forest. {name} brought a notebook to draw all the amazing things in nature.

As {name} walked along the forest path, wonderful discoveries appeared everywhere! A family of rabbits hopped by, colorful butterflies danced on flowers, and a wise old owl watched from a tall tree.

{name} sat by a peaceful stream and noticed how everything in nature was connected—the trees gave homes to birds, the flowers fed the bees, and the stream gave water to all the plants and animals.

Drawing pictures of all these discoveries, {name} felt grateful for the beautiful natural world. {name} promised to always take care of nature and teach others about its wonders.

The End."""
        }
    ],
    'share': [
        {
            'title': '{name} Learns to Share',
            'template': """It was {name}'s birthday! The {age}-year-old received the most amazing toy—a remote-controlled car that everyone wanted to play with.

At the birthday party, {name}'s friends all asked to try the new toy. At first, {name} wanted to keep it all to themselves. "It's mine!" {name} said, holding it tight.

But then {name} noticed that the friends looked sad. {name} thought about how much more fun it would be if everyone could play together. Taking a deep breath, {name} said, "Let's take turns! Everyone can drive the car."

Soon, everyone was laughing and having fun, racing the car and making up games together. {name} discovered that sharing the toy made the birthday party even more special. The joy on everyone's faces made {name} happier than keeping the toy alone ever could.

{name} learned that sharing doesn't mean losing something—it means multiplying the fun and happiness!

The End."""
        }
    ]
}


class StoryGenerator:
    """
    Handles story generation using templates or LLM APIs.
    """
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        
    def generate_story(self, theme, child_name=None, child_age=None, **kwargs):
        """
        Generate a story based on the theme and child information.
        
        Args:
            theme: Story theme (caring, courage, friendship, honest, nature, share)
            child_name: Optional child's name (default: "Your Hero")
            child_age: Optional child's age (default: 5)
            **kwargs: Additional options for future use
            
        Returns:
            dict: {
                'title': str,
                'body': str,
                'model_source': 'online' or 'offline'
            }
        """
        if self.provider == 'openai' and settings.OPENAI_API_KEY:
            return self._generate_with_openai(theme, child_name, child_age, **kwargs)
        elif self.provider == 'anthropic' and settings.ANTHROPIC_API_KEY:
            return self._generate_with_anthropic(theme, child_name, child_age, **kwargs)
        else:
            return self._generate_with_template(theme, child_name, child_age, **kwargs)
    
    def _generate_with_template(self, theme, child_name, child_age, **kwargs):
        """
        Generate story using pre-defined templates.
        """
        # Use default values if not provided
        name = child_name or "Your Hero"
        age = child_age or 5
        
        # Clamp age to reasonable range
        age = max(3, min(age, 10))
        
        # Get templates for the theme (fallback to 'friendship' if theme not found)
        theme_lower = theme.lower()
        templates = STORY_TEMPLATES.get(theme_lower, STORY_TEMPLATES['friendship'])
        
        # Select a random template
        template_data = random.choice(templates)
        
        # Fill in the template
        title = template_data['title'].format(name=name, age=age)
        body = template_data['template'].format(name=name, age=age)
        
        return {
            'title': title,
            'body': body,
            'model_source': 'offline'
        }
    
    def _generate_with_openai(self, theme, child_name, child_age, **kwargs):
        """
        Generate story using OpenAI API.
        
        To implement:
        1. pip install openai
        2. Use OpenAI chat completion with child-appropriate prompts
        3. Ensure content filtering for child safety
        """
        try:
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            
            name = child_name or "Your Hero"
            age = child_age or 5
            age = max(3, min(age, 10))
            
            prompt = f"""Write a short, age-appropriate children's story (300-800 words) about {name}, a {age}-year-old child.

Theme: {theme}

The story should:
- Be positive and educational
- Include a clear lesson about {theme}
- Be appropriate for ages 4-8
- Have a satisfying ending
- Be engaging and fun to read

Format the response as:
Title: [Story Title]

[Story body]"""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a children's story writer who creates safe, educational, and engaging stories for young children."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.8
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse title and body
            if "Title:" in content:
                parts = content.split("\n", 2)
                title = parts[0].replace("Title:", "").strip()
                body = parts[2].strip() if len(parts) > 2 else parts[1].strip()
            else:
                lines = content.split("\n")
                title = lines[0].strip()
                body = "\n".join(lines[1:]).strip()
            
            return {
                'title': title,
                'body': body,
                'model_source': 'online'
            }
            
        except Exception as e:
            print(f"OpenAI generation failed: {e}. Falling back to template.")
            return self._generate_with_template(theme, child_name, child_age, **kwargs)
    
    def _generate_with_anthropic(self, theme, child_name, child_age, **kwargs):
        """
        Generate story using Anthropic Claude API.
        
        To implement:
        1. pip install anthropic
        2. Use Claude with child-appropriate prompts
        """
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            
            name = child_name or "Your Hero"
            age = child_age or 5
            age = max(3, min(age, 10))
            
            prompt = f"""Write a short, age-appropriate children's story (300-800 words) about {name}, a {age}-year-old child.

Theme: {theme}

The story should:
- Be positive and educational
- Include a clear lesson about {theme}
- Be appropriate for ages 4-8
- Have a satisfying ending
- Be engaging and fun to read

Please provide the story with a title."""
            
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = message.content[0].text.strip()
            
            # Parse title and body (simple heuristic)
            lines = content.split("\n")
            title = lines[0].strip().replace("#", "").strip()
            body = "\n".join(lines[1:]).strip()
            
            return {
                'title': title,
                'body': body,
                'model_source': 'online'
            }
            
        except Exception as e:
            print(f"Anthropic generation failed: {e}. Falling back to template.")
            return self._generate_with_template(theme, child_name, child_age, **kwargs)
