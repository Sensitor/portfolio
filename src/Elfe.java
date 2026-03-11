public class Elfe extends Race {
    public Elfe() {
        super("Elfe");
    }

    @Override
    public void appliquerModificateurs(Personnage p) {
        p.getDexterite().set(p.getDexterite().get() + 2);
        p.getForce().set(p.getForce().get() - 2);
    }
}
