import { XStack, H2, YStack, Text, H4, Card, Button, Image } from "tamagui";
import { useSafeAreaInsets } from "react-native-safe-area-context";

export default function StoryScreen() {
    const insets = useSafeAreaInsets();
    return (
        <>
            <YStack flex={1} pt={30} px={16} bg='#d9d9d9' alignItems='center' justifyContent='flex-start' style={{ paddingTop: insets.top + 10 }}>
                <YStack alignItems='center' justify={'center'} alignItems='center' mb={200}>
                    <Image source={require('../../assets/images/Background/AC-Magic Village.png')} width='250' height='250' ></Image>
                    <H4 fontWeight="bold" color="#404040" >Dogs loves the key</H4>
                    <Text>
                        I am dog. Bark bark bark. I love the key. The key.
                    </Text>
                </YStack>
                <XStack width={'100%'} justifyContent='center' alignItems='center' marginTop="auto">
                    <Button>left</Button>
                    <Button>middle</Button>
                    <Button>right</Button>
                </XStack>
                {/* <XStack position="absolute" top={40} right={16} alignItems="center" justifyContent="center" width={250} height={250} bg="#ffffffaa">
                    <Image source={require('../../assets/images/Characters/AC-Angel.png')} width={24} height={24} />   
                    <Image source={require('../../assets/images/Characters/AC-Cat.png')} width={24} height={24} />   
                    <Image source={require('../../assets/images/Characters/AC-Dog.png')} width={24} height={24} />   
                </XStack>     */}
            </YStack>
        </>
    )
}