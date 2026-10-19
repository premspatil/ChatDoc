export default function Spinner({ label, small = false }) {
  return (
    <span className="spinner-wrap" role="status">
      <span className={small ? "spinner spinner-sm" : "spinner"} />
      {label && <span className="spinner-label">{label}</span>}
    </span>
  );
}
