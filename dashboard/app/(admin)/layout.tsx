import Sidebar from "@/components/Sidebar";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto overflow-x-hidden bg-slate-50/50">
        <div className="p-10 animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
}
