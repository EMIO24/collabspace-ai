export function formatDateISO(dateString) {
  const d = new Date(dateString);
  return d.toLocaleString();
}
