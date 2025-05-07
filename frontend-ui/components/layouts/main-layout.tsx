import React from 'react';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { DashboardLayout, MobileFooter, bottomTabsList, School, schools } from '@/screens/dashboard/dashboard-layout';
import { useState } from 'react';
import { useAuth } from '@/api/authContext';

interface MainLayoutProps {
  children: React.ReactNode;
  title?: string;
  showSidebar?: boolean;
}

/**
 * MainLayout component - provides consistent navigation structure for all main screens
 *
 * @param children Content to display in the main area
 * @param title Optional title to show in the header
 * @param showSidebar Whether to show the sidebar (defaults to true)
 */
export const MainLayout = ({
  children,
  title = "Aprende Comigo",
  showSidebar = true
}: MainLayoutProps) => {
  const { userProfile } = useAuth();
  const [selectedSchool, setSelectedSchool] = useState<School>(schools[0]);

  const handleSchoolChange = (school: School) => {
    setSelectedSchool(school);
    // Here you would typically fetch data for the selected school
  };

  return (
    <SafeAreaView className="h-full w-full">
      <DashboardLayout
        title={title || selectedSchool.name}
        isSidebarVisible={showSidebar}
      >
        {children}
      </DashboardLayout>
      <MobileFooter footerIcons={bottomTabsList} />
    </SafeAreaView>
  );
};

export default MainLayout;
