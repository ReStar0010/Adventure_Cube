import React from "react";
import { ImageBackground, StyleSheet, View } from "react-native";
import { Button } from "tamagui";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";

const loginBackground = require("../assets/images/Welcome/welcome_background.png");

export default function WelcomeScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();

  return (
    <ImageBackground
      source={loginBackground}
      style={styles.container}
      resizeMode="cover"
    >
      <View style={styles.contentContainer}>
        <View style={{ paddingBottom: insets.bottom + 60, width: '100%', paddingHorizontal: 40 }}>
          <Button
            size="$6"
            bg="#5A9FD4"
            color="white"
            width="100%"
            onPress={() => router.push("/login")}
            pressStyle={{ opacity: 0.8 }}
            textAlign="center"
          >
            登入
          </Button>
        </View>
      </View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    width: "100%",
    height: "100%",
  },
  contentContainer: {
    flex: 1,
    justifyContent: "flex-end",
    alignItems: "center",
  },
});

