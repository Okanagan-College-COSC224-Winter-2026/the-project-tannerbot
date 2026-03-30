import { useState } from 'react';
import Button from './Button';
import StatusMessage from './StatusMessage';
import { createCriteria, createRubric } from '../util/api';
import './RubricCreator.css';

interface RubricCreatorProps {
    onRubricCreated?: (rubricId: number) => void;
    id: number;
    existingScoredTotal?: number;
    rubricType?: 'peer' | 'group';
}

export default function RubricCreator({
    onRubricCreated,
    id,
    existingScoredTotal = 0,
    rubricType = 'peer',
}: RubricCreatorProps) {
    const [newCriteria, setNewCriteria] = useState<Criterion[]>([{ rubricID: 0, question: '', scoreMax: 0, hasScore: true }]);
    const [criterionErrors, setCriterionErrors] = useState<Array<{ question?: string; scoreMax?: string }>>([{}]);
    const [statusMessage, setStatusMessage] = useState('');
    const [statusType, setStatusType] = useState<'error' | 'success'>('error');
    const newScoredTotal = newCriteria.reduce((sum, criterion) => {
        return sum + Math.max(0, Math.min(criterion.scoreMax, 100));
    }, 0);
    const combinedTotal = existingScoredTotal + newScoredTotal;
    const remainingPoints = Math.max(0, 100 - combinedTotal);

    const formatCriterionError = (error: { question?: string; scoreMax?: string }) => {
        const messages = [error.question, error.scoreMax].filter(Boolean);
        return messages.join(' ');
    };

    const validateCriterion = (criterion: Criterion) => {
        const errors: { question?: string; scoreMax?: string } = {};
        if (!criterion.question.trim()) {
            errors.question = 'A criterion title is required.';
        }
        if (criterion.scoreMax < 0) {
            errors.scoreMax = 'Max score cannot be negative.';
        }
        return errors;
    };

    const validateAllCriteria = (criteria: Criterion[]) => {
        const errors = criteria.map(validateCriterion);
        setCriterionErrors(errors);
        return errors.some(err => Boolean(err.question || err.scoreMax));
    };

    const handleCreate = async () => {
        try {
            setStatusMessage('');
            const hasValidationErrors = validateAllCriteria(newCriteria);
            if (hasValidationErrors) {
                setStatusType('error');
                setStatusMessage('Each criterion needs a title and a valid max score before it can be added.');
                return;
            }

            if (combinedTotal > 100) {
                setStatusType('error');
                setStatusMessage(`Total rubric score cannot exceed 100. Remaining points: ${Math.max(0, 100 - existingScoredTotal)}.`);
                return;
            }

            const rubricResponse = await createRubric(id, false, rubricType);
            const newRubricID = rubricResponse.id;
            await Promise.all(newCriteria.map(({ question, scoreMax, hasScore }) => 
                createCriteria(id, newRubricID, question, Math.max(0, Math.min(scoreMax, 100)), false, hasScore)
            ));
            setStatusType('success');
            setStatusMessage('Rubric created successfully!');
            setNewCriteria([{ rubricID: 0, question: '', scoreMax: 0, hasScore: true }]);
            setCriterionErrors([{}]);
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

        const updatedErrors = [...criterionErrors];
        updatedErrors[index] = validateCriterion(updatedCriteria[index]);
        setCriterionErrors(updatedErrors);
    };

    const handleScoreMaxChange = (index: number, value: number) => {
        const updatedCriteria = [...newCriteria];
        updatedCriteria[index].scoreMax = Math.max(0, Math.min(100, value));
        setNewCriteria(updatedCriteria);

        const updatedErrors = [...criterionErrors];
        updatedErrors[index] = validateCriterion(updatedCriteria[index]);
        setCriterionErrors(updatedErrors);
    };

    const handleAddNewSection = () => {
        const hasValidationErrors = validateAllCriteria(newCriteria);
        if (hasValidationErrors) {
            setStatusType('error');
            setStatusMessage('Add a title and valid max score before adding another criterion.');
            return;
        }

        setStatusMessage('');
        setNewCriteria(prev => [...prev, { rubricID: 0, question: '', scoreMax: 0, hasScore: true }]);
        setCriterionErrors(prev => [...prev, {}]);
    };

    const handleRemoveSection = (index: number) => {
        setNewCriteria(prev => prev.filter((_, i) => i !== index));
        setCriterionErrors(prev => prev.filter((_, i) => i !== index));
    };

    return (
        <div className="RubricCreator">
            <h2>Create New {rubricType === 'group' ? 'Group Review' : 'Peer Review'} Criteria</h2>

            <StatusMessage message={statusMessage} type={statusType} />

            <p className="remaining-points">
                Remaining points: <strong>{remainingPoints}</strong> / 100
            </p>

            {newCriteria.map((item, index) => {
                const criterionErrorMessage = formatCriterionError(criterionErrors[index] || {});

                return (
                <div key={index} className="criteria-input-block">
                    <div className="criteria-input-section card border-0 shadow-sm">
                        <div className="card-body criteria-row">
                        <input
                            type="text"
                            value={item.question}
                            onChange={(e) => handleQuestionChange(index, e.target.value)}
                            placeholder="Enter criterion point"
                            aria-invalid={Boolean(criterionErrors[index]?.question)}
                            className={criterionErrors[index]?.question ? 'invalid-input' : ''}
                        />
                        <input
                            type="number"
                            min="0"
                            max="100"
                            value={item.scoreMax === 0 ? '' : item.scoreMax}
                            onChange={(e) => handleScoreMaxChange(index, Number(e.target.value || 0))}
                            placeholder="Max Score"
                            aria-label="Max Score"
                            aria-invalid={Boolean(criterionErrors[index]?.scoreMax)}
                            className={criterionErrors[index]?.scoreMax ? 'invalid-input' : ''}
                        />
                        <Button type="secondary" onClick={() => handleRemoveSection(index)}>Remove Criterion</Button>
                        </div>
                    </div>
                    {criterionErrorMessage && (
                        <StatusMessage
                            message={criterionErrorMessage}
                            type="error"
                            className="criteria-row-error"
                        />
                    )}
                </div>
                );
            })}

            <div className="button-group">
                <Button onClick={handleAddNewSection}>Add New Criterion</Button>
                <Button onClick={handleCreate}>Create</Button>
            </div>
        </div>
    );
} 