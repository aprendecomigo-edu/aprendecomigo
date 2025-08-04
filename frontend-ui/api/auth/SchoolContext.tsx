import React, { createContext, useContext, useState, useEffect } from 'react';

import { useUserProfile } from './UserProfileContext';

export interface UserSchool {
  id: number;
  name: string;
  role: string;
  role_display: string;
}

interface SchoolContextType {
  userSchools: UserSchool[];
  currentSchool: UserSchool | null;
  setCurrentSchool: (school: UserSchool) => void;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  isSchoolAdmin: boolean;
  isTeacher: boolean;
}

const SchoolContext = createContext<SchoolContextType | undefined>(undefined);

export const SchoolProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { userProfile } = useUserProfile();
  const [userSchools, setUserSchools] = useState<UserSchool[]>([]);
  const [currentSchool, setCurrentSchoolState] = useState<UserSchool | null>(null);

  // Extract schools from user profile roles
  useEffect(() => {
    if (userProfile?.roles) {
      const schools: UserSchool[] = userProfile.roles.map((role: any) => ({
        id: role.school.id,
        name: role.school.name,
        role: role.role,
        role_display: role.role_display,
      }));

      setUserSchools(schools);
      
      // Set current school to first admin school, or first school if no admin schools
      const adminSchools = schools.filter(s => s.role === 'school_owner' || s.role === 'school_admin');
      const defaultSchool = adminSchools.length > 0 ? adminSchools[0] : schools[0];
      if (defaultSchool && !currentSchool) {
        setCurrentSchoolState(defaultSchool);
      }
    } else {
      setUserSchools([]);
      setCurrentSchoolState(null);
    }
  }, [userProfile]);

  // Clear school data when no profile
  useEffect(() => {
    if (!userProfile) {
      setUserSchools([]);
      setCurrentSchoolState(null);
    }
  }, [userProfile]);

  const setCurrentSchool = (school: UserSchool) => {
    setCurrentSchoolState(school);
  };

  const hasRole = (role: string): boolean => {
    return userSchools.some(school => school.role === role);
  };

  const hasAnyRole = (roles: string[]): boolean => {
    return userSchools.some(school => roles.includes(school.role));
  };

  const isSchoolAdmin = hasAnyRole(['school_owner', 'school_admin']);
  const isTeacher = hasRole('teacher');

  const value = {
    userSchools,
    currentSchool,
    setCurrentSchool,
    hasRole,
    hasAnyRole,
    isSchoolAdmin,
    isTeacher,
  };

  return <SchoolContext.Provider value={value}>{children}</SchoolContext.Provider>;
};

export const useSchool = (): SchoolContextType => {
  const context = useContext(SchoolContext);
  if (context === undefined) {
    throw new Error('useSchool must be used within a SchoolProvider');
  }
  return context;
};