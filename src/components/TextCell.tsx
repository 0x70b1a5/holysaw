import classNames from "classnames";
import React from "react";
import { useHsStore } from "../store/store";
interface TextCellProps {
  text: string;
  onChange: (text: string) => void;
  readonly?: boolean
  active?: boolean
  onFocus?: () => void
  placeholder?: string
  className?: string
  cindex?: number
  rindex?: number
}
const TextCell: React.FC<TextCellProps> = ({ text, onChange, readonly, active, onFocus, placeholder, className, cindex, rindex }) => {
  const { grid } = useHsStore()
  const focusChannelAndRow = (ch: number, row: number) => {
    const channel = document.getElementById(`cell-${row}-${ch}`);
    if (channel) {
      channel.focus();
    }
  }
  const onkeyup = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // SHIFT-TAB: PREV CHANNEL
    if (e.key === 'Tab' && e.shiftKey) {
      e.preventDefault();
      if (cindex === undefined || cindex < 1) return;
      if (rindex === undefined) return;
      focusChannelAndRow(cindex - 1, rindex);
    }
    // TAB: NEXT CHANNEL
    else if (e.key === 'Tab') {
      e.preventDefault();
      if (cindex === undefined) return;
      if (rindex === undefined || rindex > grid.length - 1) return;
      focusChannelAndRow(cindex + 1, rindex);
    }
    // SHIFT-ENTER: PREV ROW
    if (e.key === 'Enter' && e.shiftKey) {
      e.preventDefault();
      if (cindex === undefined) return;
      if (rindex === undefined || rindex < 1) return;
      focusChannelAndRow(cindex, rindex - 1);
    }
    // ENTER: NEXT ROW
    else if (e.key === 'Enter') {
      e.preventDefault();
      if (cindex === undefined || cindex > grid[0].cells.length - 1) return;
      if (rindex === undefined) return;
      focusChannelAndRow(cindex, rindex + 1);
    }
  }
  return (
    <textarea
      id={`cell-${rindex}-${cindex}`}
      value={text}
      onChange={(e) => onChange(e.target.value)}
      onFocus={onFocus}
      className={classNames("grow w-16", { 'bg-gray-200': readonly, 'bg-gray-100': active }, className)}
      readOnly={readonly}
      placeholder={placeholder}
      onKeyDown={onkeyup}
    ></textarea>
  );
};

export default TextCell;