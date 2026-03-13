import { useState } from 'react';
import Button from './Button';
import StatusMessage from './StatusMessage';
import { createCriteria, createRubric } from '../util/api';
import './RubricCreator.css';

interface RubricCreatorProps {
    onRubricCreated?: (rubricId: number) => void;
    id: number;
    existingScoredTotal?: number;
}

export default function RubricCreator({ onRubricCreated, id, existingScoredTotal = 0 }: RubricCreatorProps) {
    const [newCriteria, setNewCriteria] = useState<Criterion[]>([{ rubricID: 0, question: '', scoreMax: 0, hasScore: true }]);
    const [canComment, setCanComment] = useState(false);
    const [statusMessage, setStatusMessage] = useState('');
    const [statusType, setStatusType] = useState<'error' | 'success'>('error');

    const handleCreate = async () => {
        try {
            setStatusMessage('');
            const totalScored = newCriteria.reduce((sum, criterion) => {
                if (!criterion.hasScore) {
                    return sum;
                }
                return sum + Math.max(0, Math.min(criterion.scoreMax, 100));
            }, 0);

            const combinedTotal = existingScoredTotal + totalScored;

            if (combinedTotal > 100) {
                setStatusType('error');
                setStatusMessage(`Total rubric score cannot exceed 100. Remaining points: ${Math.max(0, 100 - existingScoredTotal)}.`);
                return;
            }

            const rubricResponse = await createRubric(id, canComment);
            const newRubricID = rubricResponse.id;
            await Promise.all(newCriteria.map(({ question, scoreMax, hasScore }) => 
                createCriteria(newRubricID, question, Math.max(0, Math.min(scoreMax, 100)), canComment, hasScore)
            ));
            setStatusType('success');
            setStatusMessage('Rubric created successfully!');
            setNewCriteria([{ rubricID: 0, question: '', scoreMax: 0, hasScore: true }]);
            if (onRubricCreated) {
                onRubricCreated(newRubricID);
            }
        } catch (error) {
            console.error("Error creating criteria:", error);
            setStatusType('error');
            setStatusMessage(error instanceof Error ? error.message : 'Error creating rubric.');
        }
    };

    const handleQuestionChange = (index: number, value: string) => {
        const updatedCriteria = [...newCriteria];
        updatedCriteria[index].question = value;
        setNewCriteria(updatedCriteria);
    };

    const handleScoreMaxChange = (index: number, value: number) => {
        const updatedCriteria = [...newCriteria];
        updatedCriteria[index].scoreMax = Math.max(0, Math.min(100, value));
        setNewCriteria(updatedCriteria);
    };

    const handleHasScoreChange = (index: number, value: boolean) => {
        const updatedCriteria = [...newCriteria];
        updatedCriteria[index].hasScore = value;
        if (!value) {
            updatedCriteria[index].scoreMax = 0;
        }
        setNewCriteria(updatedCriteria);
    };

    const handleAddNewSection = () => setNewCriteria(prev => [...prev, { rubricID: 0, question: '', scoreMax: 0, hasScore: true }]);

    const handleRemoveSection = (index: number) => setNewCriteria(prev => prev.filter((_, i) => i !== index));

    return (
        <div className="RubricCreator">
            <h2>Create New Criteria</h2>

            <StatusMessage message={statusMessage} type={statusType} />

            <label className="comment-checkbox">
                Reviewer can comment:
                <input
                    type="checkbox"
                    checked={canComment}
                    onChange={() => setCanComment(prev => !prev)}
                />
            </label>

            {newCriteria.map((item, index) => (
                <div key={index} className="criteria-input-section">
                    <input
                        type="text"
                        value={item.question}
                        onChange={(e) => handleQuestionChange(index, e.target.value)}
                        placeholder="Enter question"
                    />
                    <label>
                        Has score:
                        <input
                            type="checkbox"
                            checked={item.hasScore}
                            onChange={(e) => handleHasScoreChange(index, e.target.checked)}
                        />
                    </label>
                    {item.hasScore && (
                        <input
                            type="number"
                            min="0"
                            max="100"
                            value={item.scoreMax}
                            onChange={(e) => handleScoreMaxChange(index, Number(e.target.value))}
                            placeholder="Enter score max"
                        />
                    )}
                    <Button onClick={() => handleRemoveSection(index)}>Remove Criterion</Button>
                </div>
            ))}

            <div className="button-group">
                <Button onClick={handleAddNewSection}>Add New Criterion</Button>
                <Button onClick={handleCreate}>Create</Button>
            </div>
        </div>
    );
} 