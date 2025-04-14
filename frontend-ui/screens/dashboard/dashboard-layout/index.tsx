import React, { useEffect, useState } from "react";
import { Box } from "@/components/ui/box";
import { HStack } from "@/components/ui/hstack";
import { isWeb } from "@gluestack-ui/nativewind-utils/IsWeb";
import { ChevronLeftIcon, Icon, MenuIcon } from "@/components/ui/icon";
import { Text } from "@/components/ui/text";
import { VStack } from "@/components/ui/vstack";
import { Pressable } from "@/components/ui/pressable";
import type { LucideIcon } from "lucide-react-native";
import { LogOutIcon } from "lucide-react-native";
import { InboxIcon } from "./assets/icons/inbox";
import { GlobeIcon } from "./assets/icons/globe";
import { Button, ButtonText } from "@/components/ui/button";
import { Heading } from "@/components/ui/heading";
import { ScrollView } from "@/components/ui/scroll-view";
import { Divider } from "@/components/ui/divider";
import { Grid, GridItem } from "@/components/ui/grid";
import {
  Avatar,
  AvatarFallbackText,
  AvatarImage,
} from "@/components/ui/avatar";
import { router } from "expo-router";
import { HomeIcon } from "./assets/icons/home";
import { HeartIcon } from "./assets/icons/heart";
import { ProfileIcon } from "./assets/icons/profile";
import { CalendarIcon } from "./assets/icons/calendar";
import { SafeAreaView } from "@/components/ui/safe-area-view";
import { cn } from "@gluestack-ui/nativewind-utils/cn";
import { Platform, Alert } from "react-native";
import { useAuth } from "@/api/authContext";
import {
  Modal,
  ModalBackdrop,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from "@/components/ui/modal";
import { Center } from "@/components/ui/center";
import { AlertTriangleIcon } from "lucide-react-native";

type MobileHeaderProps = {
  title: string;
};

type HeaderProps = {
  title: string;
  toggleSidebar: () => void;
};

type Icons = {
  iconName: LucideIcon | typeof Icon;
};
const list: Icons[] = [
  {
    iconName: HomeIcon,
  },
  {
    iconName: InboxIcon,
  },
  {
    iconName: GlobeIcon,
  },
  {
    iconName: HeartIcon,
  },
];
type BottomTabs = {
  iconName: LucideIcon | typeof Icon;
  iconText: string;
};
const bottomTabsList: BottomTabs[] = [
  {
    iconName: HomeIcon,
    iconText: "Home",
  },

  {
    iconName: GlobeIcon,
    iconText: "Community",
  },
  {
    iconName: InboxIcon,
    iconText: "Inbox",
  },
  {
    iconName: HeartIcon,
    iconText: "Favourite",
  },
  {
    iconName: ProfileIcon,
    iconText: "Profile",
  },
];

interface CardData {
  bannerUri: string;
  title: string;
  description: string;
}
interface HolidaysCardData {
  icon: any;
  title: string;
  description: string;
}
interface LeavesCardData {
  title: string;
  description: string;
  leaves: number;
  isDisabled: boolean;
}
interface ColleaguesCardData {
  image: any;
  title: string;
  position: string;
}

const HeadingCards: CardData[] = [
  {
    bannerUri: require("@/assets/dashboard/dashboard-layout/image.png"),
    title: "Update your profile",
    description: "Add your details",
  },
  {
    bannerUri: require("@/assets/dashboard/dashboard-layout/image2.png"),
    title: "Your skills",
    description: "Add your skills here",
  },
  {
    bannerUri: require("@/assets/dashboard/dashboard-layout/image3.png"),
    title: "Your goals",
    description: "Set a target to accomplish",
  },
  {
    bannerUri: require("@/assets/dashboard/dashboard-layout/image3.png"),
    title: "Your goals",
    description: "Set a target to accomplish",
  },
  {
    bannerUri: require("@/assets/dashboard/dashboard-layout/image3.png"),
    title: "Your goals",
    description: "Set a target to accomplish",
  },
];
const HolidaysCards: HolidaysCardData[] = [
  {
    icon: CalendarIcon,
    title: "Navaratri",
    description: "12 March, Monday (Optional holiday)",
  },
  {
    icon: CalendarIcon,
    title: "Durga Puja",
    description: "12 October, Tuesday",
  },
  {
    icon: CalendarIcon,
    title: "Diwali",
    description: "12 March, Wednesday",
  },
  {
    icon: CalendarIcon,
    title: "Christmas",
    description: "12 March, Thursday",
  },
];
const LeavesCards: LeavesCardData[] = [
  {
    title: "Earned Leaves",
    description: "Available 24",
    leaves: 24,
    isDisabled: false,
  },
  {
    title: "Sick Leaves",
    description: "Available 24",
    leaves: 24,
    isDisabled: false,
  },
  {
    title: "Menstrual Leaves",
    description: "Available 20",
    leaves: 20,
    isDisabled: false,
  },
  {
    title: "Optional Leaves",
    description: "Available 0",
    leaves: 0,
    isDisabled: true,
  },
];
const ColleaguesCards: ColleaguesCardData[] = [
  {
    image: require("@/assets/dashboard/dashboard-layout/image7.png"),
    title: "Emily Zho",
    position: "UI/UX Designer",
  },
  {
    image: require("@/assets/dashboard/dashboard-layout/image4.png"),
    title: "Marilyn Monroe",
    position: "SDE II",
  },
  {
    image: require("@/assets/dashboard/dashboard-layout/image5.png"),
    title: "James Kant",
    position: "SDE III",
  },
  {
    image: require("@/assets/dashboard/dashboard-layout/image6.png"),
    title: "Richard Faynmen",
    position: "CEO Marketing",
  },
];

// Create a reusable logout button component to follow DRY principles
function LogoutButton({ displayStyle = "icon-only" }: { displayStyle?: "icon-only" | "icon-with-text" | "button" }) {
  const { logout } = useAuth();
  const [showModal, setShowModal] = useState(false);

  const handlePressLogout = () => {
    setShowModal(true);
  };

  const handleConfirmLogout = async () => {
    setShowModal(false); // Close modal first

    // Short timeout to allow the modal to close smoothly
    setTimeout(async () => {
      try {
        await logout();
      } catch (error) {
        console.error('Error during logout:', error);
      }
    }, 150);
  };

  const handleCancelLogout = () => {
    setShowModal(false);
  };

  // Render the confirmation modal
  const renderModal = () => {
    return (
      <Modal isOpen={showModal} onClose={handleCancelLogout}>
        <ModalBackdrop />
        <ModalContent className="p-6">
          <ModalHeader>
            <Heading size="lg">Confirm Logout</Heading>
            <ModalCloseButton>
              <Icon as={ChevronLeftIcon} />
            </ModalCloseButton>
          </ModalHeader>
          <ModalBody>
            <Center>
              <Icon
                as={AlertTriangleIcon}
                className="w-14 h-14 mb-4 text-amber-500"
              />
              <Text className="text-center mb-2">
                Are you sure you want to log out?
              </Text>
              <Text className="text-center text-sm text-typography-500">
                You will need to sign in again to access your account.
              </Text>
            </Center>
          </ModalBody>
          <ModalFooter>
            <Button
              variant="outline"
              action="secondary"
              className="flex-1 mr-2"
              onPress={handleCancelLogout}
            >
              <ButtonText>Cancel</ButtonText>
            </Button>
            <Button
              action="negative"
              className="flex-1 ml-2"
              onPress={handleConfirmLogout}
            >
              <ButtonText>Logout</ButtonText>
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    );
  };

  if (displayStyle === "button") {
    return (
      <>
        <Button
          size="sm"
          variant="outline"
          action="negative"
          onPress={handlePressLogout}
          className="border-error-600"
        >
          <HStack space="xs" className="items-center">
            <Icon as={LogOutIcon} className="w-4 h-4 stroke-error-700" />
            <ButtonText className="text-error-700">Logout</ButtonText>
          </HStack>
        </Button>
        {renderModal()}
      </>
    );
  }

  if (displayStyle === "icon-with-text") {
    return (
      <>
        <Pressable
          className="bg-error-50 rounded-md p-2 mb-4 w-11 hover:bg-error-100"
          onPress={handlePressLogout}
        >
          <VStack className="items-center" space="xs">
            <Icon
              as={LogOutIcon}
              className="w-6 h-6 stroke-error-700"
            />
            <Text className="text-[10px] text-error-700 font-medium">Logout</Text>
          </VStack>
        </Pressable>
        {renderModal()}
      </>
    );
  }

  // Default icon-only
  return (
    <>
      <Pressable
        className="bg-error-50 rounded-full p-2"
        onPress={handlePressLogout}
      >
        <Icon
          as={LogOutIcon}
          className="w-5 h-5 stroke-error-700"
        />
      </Pressable>
      {renderModal()}
    </>
  );
}

const Sidebar = () => {
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  
  const handlePress = (index: number) => {
    setSelectedIndex(index);
    // Add navigation logic based on index if needed
  };

  return (
    <VStack
      className="w-14 pt-5 h-full items-center border-r border-border-300 pb-5"
      space="xl"
    >
      <VStack className="items-center" space="xl">
        {list.map((item, index) => {
          return (
            <Pressable
              key={index}
              className="hover:bg-background-50"
              onPress={() => handlePress(index)}
            >
              <Icon
                as={item.iconName}
                className={`w-[55px] h-9 stroke-background-800
                ${index === selectedIndex ? "fill-background-800" : "fill-none"}

                `}
              />
            </Pressable>
          );
        })}
      </VStack>

      <Box className="flex-1" />
      
      <LogoutButton displayStyle="icon-with-text" />
    </VStack>
  );
};

const DashboardLayout = (props: any) => {
  const [isSidebarVisible, setIsSidebarVisible] = useState(
    props.isSidebarVisible
  );
  function toggleSidebar() {
    setIsSidebarVisible(!isSidebarVisible);
  }
  return (
    <VStack className="h-full w-full bg-background-0">
      <Box className="md:hidden">
        <MobileHeader title={props.title} />
      </Box>
      <Box className="hidden md:flex">
        <WebHeader toggleSidebar={toggleSidebar} title={props.title} />
      </Box>
      <VStack className="h-full w-full">
        <HStack className="h-full w-full">
          <Box className="hidden md:flex h-full">
            {isSidebarVisible && <Sidebar />}
          </Box>
          <VStack className="w-full">{props.children}</VStack>
        </HStack>
      </VStack>
    </VStack>
  );
};

function MobileFooter({ footerIcons }: { footerIcons: any }) {
  return (
    <HStack
      className={cn(
        "bg-background-0 justify-between w-full absolute left-0 bottom-0 right-0 p-3 overflow-hidden items-center  border-t-border-300  md:hidden border-t",
        { "pb-5": Platform.OS === "ios" },
        { "pb-5": Platform.OS === "android" }
      )}
    >
      {footerIcons.map(
        (
          item: { iconText: string; iconName: any },
          index: React.Key | null | undefined
        ) => {
          return (
            <Pressable
              className="px-0.5 flex-1 flex-col items-center"
              key={index}
              onPress={() => router.push("/dashboard/dashboard-layout")}
            >
              <Icon
                as={item.iconName}
                size="md"
                className="h-[32px] w-[65px]"
              />
              <Text className="text-xs text-center text-typography-600">
                {item.iconText}
              </Text>
            </Pressable>
          );
        }
      )}
    </HStack>
  );
}

function WebHeader(props: HeaderProps) {
  return (
    <HStack className="pt-4 pr-10 pb-3 bg-background-0 items-center justify-between border-b border-border-300">
      <HStack className="items-center">
        <Pressable
          onPress={() => {
            props.toggleSidebar();
          }}
        >
          <Icon as={MenuIcon} size="lg" className="mx-5" />
        </Pressable>
        <Text className="text-2xl">{props.title}</Text>
      </HStack>

      <HStack space="md" className="items-center">
        <LogoutButton displayStyle="button" />
        <Avatar className="h-9 w-9">
          <AvatarFallbackText className="font-light">A</AvatarFallbackText>
        </Avatar>
      </HStack>
    </HStack>
  );
}

function MobileHeader(props: MobileHeaderProps) {
  return (
    <HStack
      className="py-6 px-4 border-b border-border-50 bg-background-0 items-center justify-between"
    >
      <HStack space="md" className="items-center">
        <Pressable
          onPress={() => {
            router.back();
          }}
        >
          <Icon as={ChevronLeftIcon} />
        </Pressable>
        <Text className="text-xl">{props.title}</Text>
      </HStack>
      
      <LogoutButton displayStyle="icon-only" />
    </HStack>
  );
}

const MainContent = () => {
  return (
    <Box className="flex-1 ">
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{
          paddingBottom: isWeb ? 0 : 100,
          flexGrow: 1,
        }}
        className="flex-1 mb-20 md:mb-2"
      >
        <VStack className="p-4 pb-0 md:px-10 md:pt-6  w-full" space="2xl">
          <Heading size="2xl" className="font-roboto">
            Welcome Alexander
          </Heading>

          <Grid className="gap-5" _extra={{ className: ""}}>
            {HeadingCards.map((item, index) => {
              return (
                <GridItem
                  _extra={{
                    className: "col-span-12 sm:col-span-6 lg:col-span-4",
                  }}
                  key={index}
                >
                  <HStack
                    space="md"
                    className="border border-border-300 rounded-lg p-4 items-center justify-between"
                  >
                    <HStack space="xl" className="items-center">
                      <Avatar>
                        <AvatarImage
                          height={100}
                          width={100}
                          //@ts-ignore
                          source={item.bannerUri}
                        />
                      </Avatar>
                      <VStack>
                        <Text className="font-semibold text-typography-900 line-clamp-1">
                          {item.title}
                        </Text>
                        <Text className="line-clamp-1">{item.description}</Text>
                      </VStack>
                    </HStack>
                    <Button size="xs">
                      <ButtonText>Edit</ButtonText>
                    </Button>
                  </HStack>
                </GridItem>
              );
            })}
          </Grid>

          <Box className="bg-background-50 p-4 rounded-md">
            <Text className="text-center font-medium">
              To view analytics you need client ID. Add it to your settings and
              you're good to go.
            </Text>
          </Box>
          <Grid className="gap-5" _extra={{ className: ""}}>
            <GridItem
              _extra={{
                className: "col-span-12 sm:col-span-6 lg:col-span-4",
              }}
            >
              <VStack
                className="border border-border-300 rounded-lg px-4 py-6 items-center justify-between"
                space="sm"
              >
                <Box className="self-start  w-full px-4">
                  <Heading
                    size="lg"
                    className="font-roboto  text-typography-700"
                  >
                    Upcoming Holidays
                  </Heading>
                </Box>
                <Divider />
                {HolidaysCards.map((item, index) => {
                  return (
                    <HStack space="lg" key={index} className="w-full px-4 py-2">
                      <Avatar className="bg-background-50 h-10 w-10">
                        <Icon as={item.icon} />
                      </Avatar>
                      <VStack>
                        <Text className="text-typography-900 font-roboto line-clamp-1">
                          {item.title}
                        </Text>
                        <Text className="text-sm font-roboto line-clamp-1">
                          {item.description}
                        </Text>
                      </VStack>
                    </HStack>
                  );
                })}
              </VStack>
            </GridItem>
            <GridItem
              _extra={{
                className: "col-span-12 sm:col-span-6 lg:col-span-4",
              }}
            >
              <VStack
                className="border border-border-300 rounded-lg px-4 py-6 items-center justify-between"
                space="sm"
              >
                <Box className="self-start  w-full px-4">
                  <Heading
                    size="lg"
                    className="font-roboto  text-typography-700"
                  >
                    Your Leaves
                  </Heading>
                </Box>
                <Divider />
                {LeavesCards.map((item, index) => {
                  return (
                    <HStack
                      space="lg"
                      key={index}
                      className="w-full px-4 py-2 justify-between items-center"
                    >
                      <HStack space="xl" className="items-center">
                        <Box
                          className={cn(
                            "rounded-full h-10 w-10 items-center justify-center",
                            { "bg-success-0": item.leaves !== 0 },
                            { "bg-error-50": item.leaves === 0 }
                          )}
                        >
                          <Text
                            className={cn(
                              { "text-success-800": item.leaves !== 0 },
                              { "text-error-700": item.leaves === 0 }
                            )}
                          >
                            {item.leaves}
                          </Text>
                        </Box>
                        <VStack>
                          <Text className="text-typography-900 font-roboto line-clamp-1">
                            {item.title}
                          </Text>
                          <Text className="text-sm font-roboto line-clamp-1">
                            {item.description}
                          </Text>
                        </VStack>
                      </HStack>
                      <Button
                        isDisabled={item.isDisabled}
                        variant="outline"
                        action="secondary"
                        size="xs"
                      >
                        <ButtonText>Apply</ButtonText>
                      </Button>
                    </HStack>
                  );
                })}
              </VStack>
            </GridItem>
            <GridItem
              _extra={{
                className: "col-span-12 sm:col-span-6 lg:col-span-4",
              }}
            >
              <VStack
                className="border border-border-300  rounded-lg px-4 py-6 items-center justify-between"
                space="sm"
              >
                <Box className="self-start  w-full px-4">
                  <Heading
                    size="lg"
                    className="font-roboto  text-typography-700"
                  >
                    New colleagues
                  </Heading>
                </Box>
                <Divider />
                {ColleaguesCards.map((item, index) => {
                  return (
                    <HStack space="lg" key={index} className="w-full px-4 py-2">
                      <Avatar className="h-10 w-10">
                        <AvatarImage
                          height={100}
                          width={100}
                          source={item.image}
                        />
                      </Avatar>
                      <VStack>
                        <Text className="text-typography-900 font-roboto line-clamp-1">
                          {item.title}
                        </Text>
                        <Text className="text-sm font-roboto line-clamp-1">
                          {item.position}
                        </Text>
                      </VStack>
                    </HStack>
                  );
                })}
              </VStack>
            </GridItem>
            <GridItem
              _extra={{
                className: "col-span-12 sm:col-span-6 lg:col-span-4",
              }}
            >
              <VStack
                className="border border-border-300 rounded-lg px-4 py-6 items-center justify-between"
                space="sm"
              >
                <Box className="self-start w-full px-4">
                  <Heading
                    size="lg"
                    className="font-roboto  text-typography-700"
                  >
                    New colleagues
                  </Heading>
                </Box>
                <Divider />
                {ColleaguesCards.map((item, index) => {
                  return (
                    <HStack space="lg" key={index} className="px-4 py-2 w-full">
                      <Avatar className="h-10 w-10">
                        <AvatarImage
                          height={100}
                          width={100}
                          source={item.image}
                        />
                      </Avatar>
                      <VStack>
                        <Text className="text-typography-900 font-roboto line-clamp-1">
                          {item.title}
                        </Text>
                        <Text className="text-sm font-roboto line-clamp-1">
                          {item.position}
                        </Text>
                      </VStack>
                    </HStack>
                  );
                })}
              </VStack>
            </GridItem>
          </Grid>
        </VStack>
      </ScrollView>
    </Box>
  );
};

export const Dashboard = () => {
  // Get user profile data
  const { userProfile } = useAuth();
  
  return (
    <SafeAreaView className="h-full w-full">
      <DashboardLayout title="Dashboard" isSidebarVisible={true}>
        <MainContent />
      </DashboardLayout>
      <MobileFooter footerIcons={bottomTabsList} />
    </SafeAreaView>
  );
};
