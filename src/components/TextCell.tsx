import classNames from "classnames";

interface TextCellProps {
  text: string;
  onChange: (text: string) => void;
  readonly?: boolean
  active?: boolean
  onFocus?: () => void
  placeholder?: string
}
const TextCell: React.FC<TextCellProps> = ({ text, onChange, readonly, active, onFocus, placeholder }) => {
  return (
    <input
      type="text"
      value={text}
      onChange={(e) => onChange(e.target.value)}
      onFocus={onFocus}
      className={classNames("border border-gray-300 p-2 m-0 w-16 border-l-0 border-t-0", { 'bg-gray-200': readonly, 'bg-gray-100': active })}
      readOnly={readonly}
      placeholder={placeholder}
    />
  );
};

export default TextCell;