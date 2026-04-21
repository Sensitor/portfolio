public class Halfelin extends Race {
    public Halfelin() {
        super("Halfelin");
    }

    @Override
    public void appliquerModificateurs(Personnage p) {
        p.getForce().set(p.getForce().get() - 2);
        p.getDexterite().set(p.getDexterite().get() + 2);
    }
}
