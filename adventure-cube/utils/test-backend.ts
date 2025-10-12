/**
 * Backend Connection Test Utility
 * Run this to verify your backend is accessible
 */

import { apiClient, AssetsService, StoryService } from '../services';

export async function testBackendConnection() {
    console.log('=== Testing Backend Connection ===\n');

    const results = {
        healthCheck: false,
        themes: false,
        storyGeneration: false,
    };

    try {
        // Test 1: Health check
        console.log('1. Testing health check...');
        results.healthCheck = await apiClient.healthCheck();
        console.log(results.healthCheck ? '✅ Health check passed' : '❌ Health check failed');
    } catch (error) {
        console.error('❌ Health check error:', error);
    }

    try {
        // Test 2: Fetch themes
        console.log('\n2. Testing theme fetching...');
        const themes = await AssetsService.fetchThemes();
        results.themes = themes.length > 0;
        console.log(results.themes
            ? `✅ Themes fetched (${themes.length} themes available)`
            : '❌ No themes returned'
        );
        if (themes.length > 0) {
            console.log('   Available themes:', themes.map(t => t.name).join(', '));
        }
    } catch (error) {
        console.error('❌ Theme fetching error:', error);
    }

    try {
        // Test 3: Generate a test story
        console.log('\n3. Testing story generation...');
        const result = await StoryService.generateStory(
            'Test Story',
            { name: 'Friendship', image: null },
            { name: 'Cat', image: null },
            { name: 'Forest', image: null },
            'Test User',
            5
        );
        results.storyGeneration = !!result.story.generatedStory;
        console.log(results.storyGeneration
            ? '✅ Story generation successful'
            : '❌ Story generation failed'
        );
        if (results.storyGeneration) {
            console.log('   Story title:', result.backendData.title);
            console.log('   Model source:', result.backendData.model_source);
            console.log('   Story length:', result.backendData.body.length, 'characters');
        }
    } catch (error) {
        console.error('❌ Story generation error:', error);
    }

    // Summary
    console.log('\n=== Test Summary ===');
    const passed = Object.values(results).filter(Boolean).length;
    const total = Object.keys(results).length;
    console.log(`${passed}/${total} tests passed`);

    if (passed === total) {
        console.log('✅ All tests passed! Backend is ready to use.');
    } else {
        console.log('⚠️ Some tests failed. Check backend configuration and ensure server is running.');
        console.log('   Backend URL:', apiClient['baseUrl']);
    }

    return results;
}

// Simpler version for quick checks
export async function quickHealthCheck(): Promise<boolean> {
    try {
        return await apiClient.healthCheck();
    } catch {
        return false;
    }
}
