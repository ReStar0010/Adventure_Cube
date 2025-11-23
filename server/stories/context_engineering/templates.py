"""
Template loader for Context Engineering templates.
Loads and parses markdown templates from Context_Engineering folder.
"""
import re
from pathlib import Path
from django.conf import settings


class ContextTemplateLoader:
    """Loads and parses context engineering templates."""
    
    def __init__(self):
        # Get the base directory (parent of server)
        base_dir = Path(settings.BASE_DIR).parent
        self.templates_dir = base_dir / 'Context_Engineering'
        self._cache = {}  # Cache loaded templates
    
    def load_template(self, template_name='5min_basic'):
        """
        Load a context engineering template from markdown file.
        
        Args:
            template_name: Name of template (without .md extension)
        
        Returns:
            dict: {
                'system_prompt': str,
                'user_prompt_template': str,
                'structure': {
                    'intro_goal': str,
                    'problem_obstacle': str,
                    'effort_effort': str,
                    'climax_climax': str,
                    'ending_ending': str
                }
            }
        """
        # Check cache first
        if template_name in self._cache:
            print(f"📦 Using cached template: {template_name}")
            return self._cache[template_name]
        
        template_file = self.templates_dir / f"{template_name}.md"
        print(f"🔍 Looking for template at: {template_file}")
        print(f"   Template directory: {self.templates_dir}")
        print(f"   Template exists: {template_file.exists()}")
        
        if not template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_file}")
        
        print(f"📄 Reading template file: {template_file}")
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"   File size: {len(content)} chars")
        
        # Parse template
        template_data = self._parse_template(content)
        
        print(f"✅ Template parsed successfully:")
        print(f"   System prompt: {len(template_data['system_prompt'])} chars")
        print(f"   User prompt: {len(template_data['user_prompt_template'])} chars")
        print(f"   Structure sections: {len(template_data['structure'])}")
        
        # Cache it
        self._cache[template_name] = template_data
        
        return template_data
    
    def _parse_template(self, content):
        """Parse markdown template content."""
        # Extract system prompt
        system_prompt_match = re.search(
            r'^# system_prompt\s*\n(.*?)(?=^# |\Z)',
            content,
            re.MULTILINE | re.DOTALL
        )
        system_prompt = system_prompt_match.group(1).strip() if system_prompt_match else ""
        
        # Extract user prompt
        user_prompt_match = re.search(
            r'^# user_prompt\s*\n(.*?)(?=\Z)',
            content,
            re.MULTILINE | re.DOTALL
        )
        user_prompt_template = user_prompt_match.group(1).strip() if user_prompt_match else ""
        
        # Extract story structure definitions
        structure = self._extract_structure(content)
        
        return {
            'system_prompt': system_prompt,
            'user_prompt_template': user_prompt_template,
            'structure': structure
        }
    
    def _extract_structure(self, content):
        """Extract paragraph structure definitions from template."""
        structure = {
            'intro_goal': '',
            'problem_obstacle': '',
            'effort_effort': '',
            'climax_climax': '',
            'ending_ending': ''
        }
        
        # Pattern to match numbered list items with paragraph descriptions
        patterns = {
            'intro_goal': r'1\.\s*Intro Goal[：:]\s*\*\*(.*?)\*\*\.\s*(.*?)(?=\n2\.|\Z)',
            'problem_obstacle': r'2\.\s*Problem Obstacle[：:]\s*\*\*(.*?)\*\*\.\s*(.*?)(?=\n3\.|\Z)',
            'effort_effort': r'3\.\s*Effort Effort[：:]\s*\*\*(.*?)\*\*\.\s*(.*?)(?=\n4\.|\Z)',
            'climax_climax': r'4\.\s*Climax Climax[：:]\s*\*\*(.*?)\*\*\.\s*(.*?)(?=\n5\.|\Z)',
            'ending_ending': r'5\.\s*Ending Ending[：:]\s*\*\*(.*?)\*\*\.\s*(.*?)(?=\Z)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
            if match:
                # Combine the bold title and description
                structure[key] = f"{match.group(1).strip()}. {match.group(2).strip()}"
        
        return structure
    
    def list_available_templates(self):
        """List all available template files."""
        if not self.templates_dir.exists():
            return []
        
        templates = []
        for file in self.templates_dir.glob('*.md'):
            templates.append(file.stem)
        
        return sorted(templates)

