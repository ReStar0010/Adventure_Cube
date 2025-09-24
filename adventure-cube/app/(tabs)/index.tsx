import React from 'react';
import { YStack, H2, Text, Button } from 'tamagui';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Image } from 'expo-image';

export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();

  const handleGetStarted = () => {
    router.push('/library');
  };

  return (
    <YStack flex={1} bg='#d9d9d9' style={{ paddingTop: insets.top + 10 }} alignItems='center' justifyContent='center' px={16}>
      <YStack alignItems='center' gap={20}>
        <Image
          source={require('@/assets/images/partial-react-logo.png')}
          style={{ width: 200, height: 130 }}
        />

        <H2 color='#404040' fontWeight={'bold'} textAlign="center">
          Adventure Cube
        </H2>

        <Text color='#404040' textAlign="center" fontSize={16}>
          Create amazing interactive stories with characters, backgrounds, themes, and key items.
        </Text>

        <Text color='#666' textAlign="center" fontSize={14}>
          Choose your adventure elements and let AI generate unique stories for you!
        </Text>

        <Button
          onPress={handleGetStarted}
          bg='#5A9FD4'
          color='white'
          size="$5"
          mt={20}
        >
          Get Started
        </Button>
      </YStack>
    </YStack>
  );
}
