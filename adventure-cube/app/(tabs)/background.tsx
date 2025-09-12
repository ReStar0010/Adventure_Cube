import { XStack, H2, YStack, Text, H4, Card, Button, Image, ScrollView, Group } from "tamagui";
import { Dices, CheckCircle2, ArrowLeft, ArrowRight } from 'lucide-react-native'

export default function BackgroundScreen() {
    return (
        <>
            <YStack flex={1} pt={30} px={16} bg='#d9d9d9'>

                <XStack ai="center" gap={8} items={'center'}>
                    <ArrowLeft color='#404040' size={24} />
                    <H4 color='#404040' fontWeight={'bold'}>
                        背景
                    </H4>
                </XStack>

                <YStack gap={16} mt={20}>
                    {/* Button group */}
                    <XStack items="center" gap={10}>

                        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ width: 300 }} contentContainerStyle={{ overflow: 'hidden' }}>
                            <Group orientation="horizontal">
                                <Group.Item>
                                    <Button>First</Button>
                                </Group.Item>
                                <Group.Item>
                                    <Button>Second</Button>
                                </Group.Item>
                                <Group.Item>
                                    <Button>Third</Button>
                                </Group.Item>
                                <Group.Item>
                                    <Button>Third</Button>
                                </Group.Item>
                                <Group.Item>
                                    <Button>Third</Button>
                                </Group.Item>
                                <Group.Item>
                                    <Button>Third</Button>
                                </Group.Item>
                                <Group.Item>
                                    <Button>Third</Button>
                                </Group.Item>
                                <Group.Item>
                                    <Button>Third</Button>
                                </Group.Item>
                                <Group.Item>
                                    <Button>Third</Button>
                                </Group.Item>
                                <Group.Item>
                                    <Button>Third</Button>
                                </Group.Item>
                                <Group.Item>
                                    <Button>Third</Button>
                                </Group.Item>
                                <Group.Item>
                                    <Button>Third</Button>
                                </Group.Item>
                                <Group.Item>
                                    <Button>Third</Button>
                                </Group.Item>
                            </Group>
                        </ScrollView>

                        <ArrowRight color='#404040' size={24} />
                    </XStack>

                    {/* Scrollable image container */}
                    <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                        <XStack gap={16} px={16}>
                            <Image width={300} height={320} src={require(`../../assets/images/Background/AC-Castel.png`)} />
                            <Image width={300} height={320} src={require(`../../assets/images/Background/AC-Castel.png`)} />
                            <Image width={300} height={320} src={require(`../../assets/images/Background/AC-Castel.png`)} />
                        </XStack>
                    </ScrollView>

                    {/* Icon stack */}
                    <XStack gap={16} justifyContent="center">
                        <Dices color='#404040' size={100} />
                        <CheckCircle2 color='#404040' size={100} />
                    </XStack>
                </YStack>

            </YStack>
        </>
    );
}
