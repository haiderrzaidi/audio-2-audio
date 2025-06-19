import { headers } from 'next/headers';
import { getAppConfig, getOrigin } from '@/lib/utils';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default async function AppLayout({ children }: AppLayoutProps) {
  const hdrs = await headers();
  const origin = getOrigin(hdrs);
  const { companyName,  } = await getAppConfig(origin);

  return (
    <>
      <header className="fixed top-0 left-0 z-50 hidden w-full flex-row justify-between p-6 md:flex">
      </header>
      {children}
    </>
  );
}
