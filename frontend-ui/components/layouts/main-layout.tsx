import React, { useState } from 'react';

import { AuthGuard } from '@/components/auth/auth-guard';
import {
  MobileNavigation,
  SideNavigation,
  TopNavigation,
  schools,
  type School,
} from '@/components/navigation';
import { useTutorial, TutorialHighlight } from '@/components/tutorial';
import { Box } from '@/components/ui/box';
import { HStack } from '@/components/ui/hstack';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { VStack } from '@/components/ui/vstack';

interface MainLayoutProps {
  children: React.ReactNode;
  _title?: string;
  showSidebar?: boolean;
  requireAuth?: boolean;
}

/**
 * MainLayout component - provides consistent navigation structure for all main screens
 * The school name will be displayed in the header via SchoolSelector component
 *
 * @param children Content to display in the main area
 * @param _title Optional page title (used for internal tracking, school name shown in header)
 * @param showSidebar Whether to show the sidebar (defaults to true)
 * @param requireAuth Whether to require authentication (defaults to true)
 */
export const MainLayout = ({
  children,
  _title = 'Dashboard',
  showSidebar = true,
  requireAuth = true,
}: MainLayoutProps) => {
  const [selectedSchool, setSelectedSchool] = useState<School>(schools[0]);
  const [isSidebarVisible, setIsSidebarVisible] = useState(showSidebar);
  const { state } = useTutorial();

  const handleSchoolChange = (school: School) => {
    setSelectedSchool(school);
    // Here you would typically fetch data for the selected school
    console.log('School changed to:', school.name);
  };

  const toggleSidebar = () => {
    setIsSidebarVisible(!isSidebarVisible);
  };

  const layoutContent = (
    <SafeAreaView className="min-h-screen w-full">
      <VStack className="min-h-screen w-full bg-background-0">
        {/* Mobile Header */}
        <Box className="md:hidden">
          <TopNavigation variant="mobile" onSchoolChange={handleSchoolChange} />
        </Box>

        {/* Web Header */}
        <Box className="hidden md:flex">
          <TopNavigation
            variant="web"
            onToggleSidebar={toggleSidebar}
            onSchoolChange={handleSchoolChange}
          />
        </Box>

        {/* Main Content Area */}
        <VStack className="flex-1 w-full">
          <HStack className="flex-1 w-full">
            {/* Desktop Sidebar */}
            <Box className="hidden md:flex flex-shrink-0">
              {isSidebarVisible && (
                <TutorialHighlight
                  id="navigation"
                  isActive={state.isActive && state.config?.steps[state.currentStep]?.id === 'navigation'}
                >
                  <SideNavigation />
                </TutorialHighlight>
              )}
            </Box>

            {/* Main Content with bottom padding for mobile navigation */}
            <VStack className="flex-1 w-full pb-20 md:pb-0">{children}</VStack>
          </HStack>
        </VStack>
      </VStack>

      {/* Mobile Footer Navigation */}
      <TutorialHighlight
        id="navigation"
        isActive={state.isActive && state.config?.steps[state.currentStep]?.id === 'navigation'}
        className="md:hidden"
      >
        <MobileNavigation />
      </TutorialHighlight>
    </SafeAreaView>
  );

  // Wrap with AuthGuard if authentication is required
  if (requireAuth) {
    return <AuthGuard>{layoutContent}</AuthGuard>;
  }

  return layoutContent;
};

export default MainLayout;
