public class Nain extends Race {
    public Nain() {
        super("Nain");
    }

    @Override
    public void appliquerModificateurs(Personnage p) {
        p.getConstitution().set(p.getConstitution().get() + 2);
        p.getDexterite().set(p.getDexterite().get() - 2);
    }
}
