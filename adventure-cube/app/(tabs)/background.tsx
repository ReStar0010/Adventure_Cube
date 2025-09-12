import { XStack, H2, YStack, Text, H4, Card, Button, Image } from "tamagui";
import { Dices, CheckCircle2 } from 'lucide-react-native'

export default function BackgroundScreen() {
    return (
        <>
            <YStack flex={1} pt={30} px={16} bg='#d9d9d9'>

                <H2 color='#404040' fontWeight={'bold'}>
                    背景
                </H2>

                <YStack my={20} items='center' gap={20}>

                </YStack>
            </YStack>
        </>
    );
}
