import React from 'react';

interface Props {
    children?: React.ReactNode
}
const ExpandoBox: React.FC<Props> = ({ children }) => {
    return (
        <div className="font-mono flex flex-col px-2 py-1 place-items-center place-content-center">
            {children}
        </div>
    );
};

export default ExpandoBox;
