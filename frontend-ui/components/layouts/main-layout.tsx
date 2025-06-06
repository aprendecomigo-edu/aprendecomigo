import React from 'react';
import { useState } from 'react';

import { useAuth } from '@/api/authContext';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { DashboardLayout, MobileFooter, bottomTabsList, School, schools } from '@/screens/dashboard/dashboard-layout';

interface MainLayoutProps {
  children: React.ReactNode;
  title?: string;
  showSidebar?: boolean;
}

/**
 * MainLayout component - provides consistent navigation structure for all main screens
 * The school name will be displayed in the header via SchoolSelector component
 *
 * @param children Content to display in the main area
 * @param title Optional page title (used for internal tracking, school name shown in header)
 * @param showSidebar Whether to show the sidebar (defaults to true)
 */
export const MainLayout = ({
  children,
  title = "Dashboard",
  showSidebar = true
}: MainLayoutProps) => {
  const { userProfile } = useAuth();
  const [selectedSchool, setSelectedSchool] = useState<School>(schools[0]);

  const handleSchoolChange = (school: School) => {
    setSelectedSchool(school);
    // Here you would typically fetch data for the selected school
    console.log('School changed to:', school.name);
  };

  return (
    <SafeAreaView className="h-full w-full">
      <DashboardLayout
        title={selectedSchool.name}
        isSidebarVisible={showSidebar}
        onSchoolChange={handleSchoolChange}
      >
        {children}
      </DashboardLayout>
      <MobileFooter footerIcons={bottomTabsList} />
    </SafeAreaView>
  );
};

export default MainLayout;
