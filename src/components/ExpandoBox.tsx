import classNames from 'classnames';
import React from 'react';

interface Props {
    children?: React.ReactNode
    className?: string
}
const ExpandoBox: React.FC<Props> = ({ children, className }) => {
    return (
        <div className={classNames("font-mono flex flex-col px-2 py-1 place-items-center place-content-center", className)}>
            {children}
        </div>
    );
};

export default ExpandoBox;
