import { redirect } from 'next/navigation';

export default async function AdminDocumentTypeFilesRedirectPage({
  params,
}: {
  params: Promise<{ sectionId: string; documentType: string }>;
}) {
  const { sectionId, documentType } = await params;
  redirect(`/admin/collections/${sectionId}/groups/${documentType}/manual`);
}
