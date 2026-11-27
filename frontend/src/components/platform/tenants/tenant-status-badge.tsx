
type TenantStatusBadgeProps = {
  isActive: boolean;
  activeLabel: string;
  suspendedLabel: string;
};

export function TenantStatusBadge({
  isActive,
  activeLabel,
  suspendedLabel,
}: TenantStatusBadgeProps) {
  return (
    <span
      className={
        isActive
          ? "rounded-full bg-green-500/10 px-2.5 py-1 text-xs font-medium text-green-700"
          : "rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground"
      }
    >
      {isActive ? activeLabel : suspendedLabel}
    </span>
  );
}
