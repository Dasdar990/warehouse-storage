export function getMovementActionLabel(action) {
  switch (action) {
    case 'deposit':
      return 'Added';
    case 'withdraw':
      return 'Removed';
    case 'move':
      return 'Moved';
    case 'edit':
      return 'Edited';
    default:
      return 'Updated';
  }
}
