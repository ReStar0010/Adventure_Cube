/**
 * Example: Story Generation Component
 * This shows how to integrate the backend API with your UI
 */

import React, { useState } from 'react';
import { View, Text, Button, ActivityIndicator, ScrollView, StyleSheet } from 'react-native';
import { useStoryGeneration } from '../../hooks/use-story-generation';
import { useAudioGeneration } from '../../hooks/use-audio-generation';
import type { StoryAsset } from '../../types/Story';

export default function StoryGenerationExample() {
    // Use the custom hooks
    const { isGenerating, error, generatedStory, backendData, generateStory, reset } = useStoryGeneration();
    const { isGenerating: isGeneratingAudio, audioUrl, generateAudio } = useAudioGeneration();

    // Example assets (replace with your actual assets)
    const [selectedTheme] = useState<StoryAsset>({ name: 'Friendship', image: null });
    const [selectedCharacter] = useState<StoryAsset>({ name: 'Cat', image: null });
    const [selectedBackground] = useState<StoryAsset>({ name: 'Forest', image: null });

    const handleGenerateStory = async () => {
        await generateStory(
            'My Adventure',
            selectedTheme,
            selectedCharacter,
            selectedBackground,
            'Emma', // child name
            6 // child age
        );
    };

    const handleGenerateAudio = async () => {
        if (backendData?.id) {
            await generateAudio(backendData.id);
        }
    };

    return (
        <ScrollView style={styles.container}>
            <Text style={styles.title}>Story Generator Example</Text>

            {/* Generate Story Button */}
            <Button
                title={isGenerating ? 'Generating...' : 'Generate Story'}
                onPress={handleGenerateStory}
                disabled={isGenerating}
            />

            {/* Loading Indicator */}
            {isGenerating && (
                <View style={styles.loadingContainer}>
                    <ActivityIndicator size="large" />
                    <Text>Generating your story...</Text>
                </View>
            )}

            {/* Error Display */}
            {error && (
                <View style={styles.errorContainer}>
                    <Text style={styles.errorText}>Error: {error}</Text>
                    <Button title="Try Again" onPress={reset} />
                </View>
            )}

            {/* Generated Story Display */}
            {generatedStory && backendData && (
                <View style={styles.storyContainer}>
                    <Text style={styles.storyTitle}>{backendData.title}</Text>
                    <Text style={styles.storyMeta}>
                        Theme: {backendData.theme} | Source: {backendData.model_source}
                    </Text>
                    <Text style={styles.storyBody}>{backendData.body}</Text>

                    {/* Audio Generation */}
                    <View style={styles.audioSection}>
                        <Button
                            title={isGeneratingAudio ? 'Generating Audio...' : 'Generate Audio Narration'}
                            onPress={handleGenerateAudio}
                            disabled={isGeneratingAudio}
                        />

                        {audioUrl && (
                            <Text style={styles.audioUrl}>Audio URL: {audioUrl}</Text>
                        )}
                    </View>

                    <Button title="Generate Another Story" onPress={reset} />
                </View>
            )}
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        padding: 20,
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 20,
    },
    loadingContainer: {
        alignItems: 'center',
        marginVertical: 20,
    },
    errorContainer: {
        backgroundColor: '#ffebee',
        padding: 15,
        borderRadius: 8,
        marginVertical: 10,
    },
    errorText: {
        color: '#c62828',
        marginBottom: 10,
    },
    storyContainer: {
        marginTop: 20,
        padding: 15,
        backgroundColor: '#f5f5f5',
        borderRadius: 8,
    },
    storyTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        marginBottom: 10,
    },
    storyMeta: {
        fontSize: 12,
        color: '#666',
        marginBottom: 15,
    },
    storyBody: {
        fontSize: 16,
        lineHeight: 24,
        marginBottom: 20,
    },
    audioSection: {
        marginVertical: 15,
        padding: 10,
        backgroundColor: '#e3f2fd',
        borderRadius: 8,
    },
    audioUrl: {
        marginTop: 10,
        fontSize: 12,
        color: '#1976d2',
    },
});
