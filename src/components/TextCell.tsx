import classNames from "classnames";
import React from "react";
interface TextCellProps {
  text: string;
  onChange: (text: string) => void;
  readonly?: boolean
  active?: boolean
  onFocus?: () => void
  placeholder?: string
  className?: string
}
const TextCell: React.FC<TextCellProps> = ({ text, onChange, readonly, active, onFocus, placeholder, className }) => {
  return (
    <textarea
      value={text}
      onChange={(e) => onChange(e.target.value)}
      onFocus={onFocus}
      className={classNames("font-mono grow p-2 m-0 w-16", { 'bg-gray-200': readonly, 'bg-gray-100': active }, className)}
      readOnly={readonly}
      placeholder={placeholder}
    ></textarea>
  );
};

export default TextCell;