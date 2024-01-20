import classNames from "classnames";
import React from "react";
interface TextCellProps {
  text: string;
  onChange: (text: string) => void;
  readonly?: boolean
  active?: boolean
  onFocus?: () => void
  placeholder?: string
}
const TextCell: React.FC<TextCellProps> = ({ text, onChange, readonly, active, onFocus, placeholder, }) => {
  return (
    <textarea
      value={text}
      onChange={(e) => onChange(e.target.value)}
      onFocus={onFocus}
      className={classNames("grow align-self-stretch p-2 m-0 w-16", { 'bg-gray-200': readonly, 'bg-gray-100': active })}
      readOnly={readonly}
      placeholder={placeholder}
    ></textarea>
  );
};

export default TextCell;